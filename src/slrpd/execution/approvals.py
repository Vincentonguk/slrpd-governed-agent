from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid

@dataclass
class ApprovalRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"   # pending | approved | rejected
    approver: Optional[str] = None
