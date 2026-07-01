from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Channel = Literal["chat", "voice", "sms", "whatsapp"]

class ChatRequest(BaseModel):
    channel: Channel = "chat"
    customer_id: str = "CUST001"
    message: str
    conversation_id: Optional[str] = None

class RetrievedDoc(BaseModel):
    policy_id: str
    title: str
    journey_type: str
    risk_class: str
    effective_date: str
    source: str
    score: float
    content: str

class ToolCallResult(BaseModel):
    tool_name: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

class AssistantDecision(BaseModel):
    intent: str
    risk_flags: List[str] = Field(default_factory=list)
    requires_authentication: bool = False
    requires_handoff: bool = False
    handoff_reason: Optional[str] = None
    recommended_next_action: str = "answer"
    tool_results: List[ToolCallResult] = Field(default_factory=list)
    retrieved_article_ids: List[str] = Field(default_factory=list)

class ChatResponse(BaseModel):
    conversation_id: str
    prompt_version: str
    model_provider: str
    channel: Channel
    customer_id: str
    answer_for_customer: str
    decision: AssistantDecision
    retrieved_docs: List[RetrievedDoc]
    redacted_user_message: str
    observability: Dict[str, Any]
