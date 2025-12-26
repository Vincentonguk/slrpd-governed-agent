from pydantic import BaseModel
from typing import Any, Dict, Optional, List

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    ok: bool
    answer: Optional[str] = None
    citations: List[Dict[str, Any]] = []
    reason: str
    state: str

class ProposeActionRequest(BaseModel):
    action: str
    payload: Dict[str, Any] = {}

class ApproveRequest(BaseModel):
    approver: str
