from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime, timezone

class AuditEvent(BaseModel):
    session_id: str
    event_type: str
    state: str
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any] = Field(default_factory=dict)
    integrity_hash: Optional[str] = None
