from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Citation(BaseModel):
    report_id: str
    title: Optional[str] = None
    page: int
    quoted_text: str

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
    latency_ms: int
    tokens_used: int
    estimated_cost_usd: float

class ChatRequest(BaseModel):
    client_id: str = Field(..., description="Unique client identifier, e.g. C-01")
    query: str = Field(..., min_length=1, description="User question or instruction")

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    confidence: float
    conflicts: List[ConflictItem] = []
    derived_values: List[DerivedValue] = []
    escalated: bool = False
    execution_metrics: Optional[ExecutionMetrics] = None

class EscalationTicket(BaseModel):
    id: Optional[int] = None
    client_id: str
    query: str
    reason: str
    confidence: float
    status: str = "open"
    created_at: Optional[str] = None

class FeedbackRequest(BaseModel):
    chat_id: int
    feedback: str = Field(..., pattern="^(up|down)$")
