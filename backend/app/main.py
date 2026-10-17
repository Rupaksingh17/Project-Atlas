import os
import time
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.models.api import ChatRequest, ChatResponse, EscalationTicket, FeedbackRequest
from backend.app.database.db import db_manager
from backend.app.services.ingest import ingest_reports
from backend.app.agents.agent_engine import agent_engine

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header"
        )
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-ingest reports on startup if empty
    from backend.app.database.vector_store import vector_store
    if vector_store.count() == 0:
        try:
            ingest_reports()
        except Exception:
            pass
    yield

app = FastAPI(
    title="Project Atlas - Report Copilot API",
    description="Entitlement-aware RAG copilot with conflict resolution and multi-agent guardrails.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Monitoring"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "database_backend": "mysql" if db_manager.use_mysql else "sqlite_fallback",
        "timestamp": int(time.time())
    }

@app.post("/chat", response_model=ChatResponse, tags=["Copilot"])
def chat_endpoint(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    start_time = time.time()
    try:
        response = agent_engine.process_query(
            client_id=request.client_id,
            query=request.query
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Log to chat_logs
        chat_id = db_manager.log_chat(
            client_id=request.client_id,
            query=request.query,
            answer=response.answer,
            confidence=response.confidence,
            escalated=response.escalated,
            latency_ms=elapsed_ms
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal agent processing error: {str(e)}")

@app.post("/ingest", tags=["Ingestion"])
def ingest_endpoint(api_key: str = Depends(verify_api_key)):
    try:
        count = ingest_reports()
        return {"status": "success", "chunks_indexed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/escalations", response_model=List[EscalationTicket], tags=["Operations"])
def list_escalations(api_key: str = Depends(verify_api_key)):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve escalations: {str(e)}")

@app.post("/feedback", tags=["Feedback"])
def submit_feedback(request: FeedbackRequest, api_key: str = Depends(verify_api_key)):
    try:
        db_manager.update_feedback(request.chat_id, request.feedback)
        return {"status": "success", "chat_id": request.chat_id, "feedback": request.feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")
