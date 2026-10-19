from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Citation(BaseModel):
    report_id: str
    title: Optional[str] = None
    page: int = Field(..., ge=1)
    quoted_text: str = Field(..., max_length=500)

class ConflictItem(BaseModel):
    metric: str
    source_a: Dict[str, Any]
    source_b: Dict[str, Any]
    difference_reason: str

class DerivedValue(BaseModel):
    metric: str
    formula: str
    assumptions: List[str]
    value: str
    nature: str = "derived_estimate"

class ExecutionMetrics(BaseModel):
    latency_ms: int = Field(..., ge=0)
    tokens_used: int = Field(..., ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0)

class ChatRequest(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$", description="Authenticated client account identifier")
    query: str = Field(..., min_length=1, max_length=8000, description="User question")

class ChatResponse(BaseModel):
    chat_id: Optional[int] = None
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    conflicts: List[ConflictItem] = Field(default_factory=list)
    derived_values: List[DerivedValue] = Field(default_factory=list)
    escalated: bool = False
    execution_metrics: Optional[ExecutionMetrics] = None

class EscalationTicket(BaseModel):
    id: Optional[int] = None
    client_id: str
    query: str
    reason: str
    confidence: float = Field(..., ge=0, le=1)
    status: str = "open"
    created_at: Optional[str] = None

class FeedbackRequest(BaseModel):
    chat_id: int = Field(..., ge=1)
    client_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    feedback: str = Field(..., pattern="^(up|down)$")
