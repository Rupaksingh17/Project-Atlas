import os
import time
import secrets
import logging
import math
from urllib.parse import urlparse
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.models.api import ChatRequest, ChatResponse, EscalationTicket, FeedbackRequest
from backend.app.database.db import db_manager
from backend.app.services.ingest import ingest_reports, IngestionBusy
from backend.app.agents.agent_engine import agent_engine
from backend.app.services.llm import answer_service

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
ops_api_key_header = APIKeyHeader(name="X-Ops-Key", auto_error=False)
logger = logging.getLogger(__name__)

def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or not settings.API_KEY or not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header"
        )
    return api_key

def verify_ops_key(api_key: str = Security(ops_api_key_header)):
    if not api_key or not settings.OPS_API_KEY or not secrets.compare_digest(api_key, settings.OPS_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-Ops-Key header")
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.API_KEY or len(settings.API_KEY) < 32 or "CHANGE_ME" in settings.API_KEY:
        raise RuntimeError("API_KEY must be configured as a random value of at least 32 characters.")
    if (not settings.OPS_API_KEY or len(settings.OPS_API_KEY) < 32 or "CHANGE_ME" in settings.OPS_API_KEY
            or secrets.compare_digest(settings.OPS_API_KEY, settings.API_KEY)):
        raise RuntimeError("OPS_API_KEY must be a different random value of at least 32 characters.")
    if answer_service is None:
        raise RuntimeError("Configure a supported language model provider before starting the API.")
    if not settings.LLM_MODEL.strip():
        raise RuntimeError("LLM_MODEL must be set.")
    if settings.LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY or "CHANGE_ME" in settings.OPENAI_API_KEY:
            raise RuntimeError("A live OpenAI-compatible provider and OPENAI_API_KEY are required.")
        provider_url = urlparse(settings.OPENAI_BASE_URL)
        if (not provider_url.hostname
                or (provider_url.scheme != "https" and provider_url.hostname not in {"localhost", "127.0.0.1"})):
            raise RuntimeError("OpenAI-compatible provider URL must use HTTPS outside localhost.")
    elif settings.LLM_PROVIDER == "ollama":
        provider_url = urlparse(settings.OLLAMA_BASE_URL)
        allowed_ollama_hosts = {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}
        if (provider_url.hostname not in allowed_ollama_hosts
                or provider_url.scheme not in {"http", "https"}):
            raise RuntimeError("Ollama must use a local host URL (localhost, host.docker.internal, or the compose service).")
    else:
        raise RuntimeError("LLM_PROVIDER must be 'openai' or 'ollama'.")
    if settings.LLM_PROVIDER == "openai" and (
        settings.LLM_INPUT_USD_PER_1M_TOKENS is None
        or settings.LLM_OUTPUT_USD_PER_1M_TOKENS is None
        or not math.isfinite(settings.LLM_INPUT_USD_PER_1M_TOKENS)
        or not math.isfinite(settings.LLM_OUTPUT_USD_PER_1M_TOKENS)
        or settings.LLM_INPUT_USD_PER_1M_TOKENS < 0
        or settings.LLM_OUTPUT_USD_PER_1M_TOKENS < 0
    ):
        raise RuntimeError("Set current input and output token prices for the configured model.")
    if settings.LLM_TIMEOUT_SECONDS < 1 or settings.REQUEST_TIMEOUT_SECONDS < 1:
        raise RuntimeError("LLM and request timeouts must be positive.")
    if not 1 <= settings.LLM_MAX_OUTPUT_TOKENS <= 4096:
        raise RuntimeError("LLM_MAX_OUTPUT_TOKENS must be between 1 and 4096.")
    if not 0 < settings.CONFIDENCE_THRESHOLD <= 1:
        raise RuntimeError("CONFIDENCE_THRESHOLD must be greater than zero and at most one.")
    try:
        database_ready = db_manager.ping()
    except Exception:
        logger.exception("Database readiness check failed; starting in degraded mode")
        database_ready = False

    # The HTTP server can still expose health while the database is unavailable.
    from backend.app.database.vector_store import vector_store
    try:
        if database_ready:
            # Reconcile the persistent vector index against the mounted corpus;
            # this also clears stale demo or removed report chunks.
            ingest_reports()
    except Exception:
        logger.exception("Initial report ingestion failed; API will start degraded")
    yield

app = FastAPI(
    title="Project Atlas - Report Copilot API",
    description="Entitlement-aware RAG copilot with conflict resolution and multi-agent guardrails.",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log unexpected failures server-side and return a non-sensitive response."""
    logger.exception("Unhandled API error for %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected service error occurred. Please try again."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

@app.get("/health", tags=["Monitoring"])
def health_check(response: Response):
    from backend.app.database.vector_store import vector_store
    try:
        database_ready = db_manager.ping()
    except Exception:
        logger.exception("Health check database ping failed")
        database_ready = False
    try:
        indexed_chunks = vector_store.count()
    except Exception:
        logger.exception("Health check vector store count failed")
        indexed_chunks = 0
    # An empty production corpus is a valid onboarding state: the portal and
    # ingestion endpoint must still start so an operator can add licensed
    # reports. Queries explain the empty-corpus state instead of inventing data.
    ready = database_ready and answer_service is not None and vector_store.is_ready()
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "healthy" if ready else "degraded",
        "app_name": settings.APP_NAME,
        "database_backend": "mysql" if db_manager.use_mysql else "sqlite_fallback",
        "llm_provider": settings.LLM_PROVIDER,
        "dataset_label": settings.DATASET_LABEL,
        "indexed_chunks": indexed_chunks,
        "corpus_status": "ready" if indexed_chunks > 0 else "empty",
        "timestamp": int(time.time())
    }

@app.post("/chat", response_model=ChatResponse, tags=["Copilot"])
def chat_endpoint(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    start_time = time.time()
    try:
        if not db_manager.client_exists(request.client_id):
            raise HTTPException(status_code=404, detail="Unknown client account")
        from backend.app.database.vector_store import vector_store
        if not vector_store.is_ready():
            raise HTTPException(status_code=503, detail="The report index is updating or unavailable. Please retry shortly.")
        response = agent_engine.process_query(
            client_id=request.client_id,
            query=request.query
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Log to chat_logs
        try:
            response.chat_id = db_manager.log_chat(
                client_id=request.client_id,
                query=request.query,
                answer=response.answer,
                confidence=response.confidence,
                escalated=response.escalated,
                latency_ms=elapsed_ms,
                tokens_used=response.execution_metrics.tokens_used if response.execution_metrics else 0,
                estimated_cost_usd=response.execution_metrics.estimated_cost_usd if response.execution_metrics else None,
            )
        except Exception:
            # Do not discard a safe answer solely because secondary history
            # persistence failed; record the issue for operations review.
            logger.exception("Chat answer was produced but could not be persisted")
        return response
    except HTTPException:
        raise
    except Exception:
        logger.exception("Agent request failed")
        raise HTTPException(status_code=500, detail="Internal agent processing error")

@app.post("/ingest", tags=["Ingestion"])
def ingest_endpoint(api_key: str = Depends(verify_ops_key)):
    try:
        count = ingest_reports()
        return {"status": "success", "chunks_indexed": count}
    except IngestionBusy:
        raise HTTPException(status_code=409, detail="A report ingestion is already in progress.")
    except Exception:
        logger.exception("Report ingestion failed")
        raise HTTPException(status_code=500, detail="Report ingestion failed. Check the service logs for details.")

@app.get("/escalations", response_model=List[EscalationTicket], tags=["Operations"])
def list_escalations(api_key: str = Depends(verify_ops_key)):
    try:
        rows = db_manager.get_escalations()
        tickets = []
        for r in rows:
            tickets.append(EscalationTicket(
                id=r.get("id"),
                client_id=r.get("client_id"),
                query=r.get("query"),
                reason=r.get("reason"),
                confidence=float(r.get("confidence", 0.0)),
                status=r.get("status", "open"),
                created_at=str(r.get("created_at"))
            ))
        return tickets
    except Exception:
        logger.exception("Escalation listing failed")
        raise HTTPException(status_code=500, detail="Unable to retrieve analyst escalations.")

@app.post("/feedback", tags=["Feedback"])
def submit_feedback(request: FeedbackRequest, api_key: str = Depends(verify_api_key)):
    try:
        updated = db_manager.update_feedback(request.chat_id, request.client_id, request.feedback)
        if not updated:
            raise HTTPException(status_code=404, detail="Chat record not found for this client")
        return {"status": "success", "chat_id": request.chat_id, "feedback": request.feedback}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Feedback recording failed")
        raise HTTPException(status_code=500, detail="Failed to record feedback")
