from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
import uuid

from .states import State
from .policies import Contracts, tac_required_events
from ..observability.events import AuditEvent
from ..observability.audit_log import append_event, read_events

@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: State = State.Discover
    destination_id: Optional[str] = None
    blocked: bool = False
    outcome: Optional[str] = None  # success | blocked | aborted-safe
    deferred_queries: List[Dict[str, Any]] = field(default_factory=list)
    actions_count: int = 0
    drop_event_types: Set[str] = field(default_factory=set)  # fault injection for TC-04

def emit(session: Session, event_type: str, data: Dict[str, Any]):
    if event_type in session.drop_event_types:
        return
    append_event(AuditEvent(session_id=session.id, event_type=event_type, state=session.state.value, data=data))

def _check_tac(session: Session, contracts: Contracts, state: State):
    required = tac_required_events(contracts.tac, state.value)
    events = read_events(session.id)
    have = {e["event_type"] for e in events if e.get("state") == state.value}
    missing = [x for x in required if x not in have]
    return missing

def step_discover(session: Session, destination_id: Optional[str]):
    session.destination_id = destination_id
    emit(session, "destination_selected", {"destination_id": destination_id})
    session.state = State.Validate

def step_validate(session: Session, contracts: Contracts) -> bool:
    deny = bool(contracts.se.get("policy", {}).get("deny_by_default", True))
    compatible = (session.destination_id is not None) if deny else True
    reason = "ok" if compatible else "missing_destination_identity"

    emit(session, "validation_result", {
        "compatible": compatible,
        "reason": reason,
        "dp": contracts.dp.get("id"),
        "se": contracts.se.get("id"),
        "cs": contracts.cs.get("id")
    })

    if not compatible:
        session.blocked = True
        session.outcome = "blocked"
        session.state = State.PostCheckAudit
        return False

    allow_sync = bool(contracts.dp.get("targets", {}).get("allow_sync", False))
    session.state = State.Sync if allow_sync else State.Arm
    return True

def step_sync(session: Session):
    emit(session, "sync_status", {"synced": True})
    session.state = State.Arm

def step_arm(session: Session, contracts: Contracts):
    emit(session, "arm_authorization", {"authorized": True, "limits": contracts.se.get("limits", {})})
    session.state = State.Deliver

def step_deliver(session: Session, in_envelope: bool = True):
    if in_envelope:
        emit(session, "deliver_summary", {"in_envelope": True, "adjustments": 0})
        session.state = State.Cooldown
    else:
        emit(session, "deliver_summary", {"in_envelope": False, "adjustments": 1, "anomaly": "out_of_envelope"})
        session.outcome = "aborted-safe"
        session.state = State.Cooldown

def step_cooldown(session: Session):
    emit(session, "cooldown_confirmed", {"cooldown": True})
    session.state = State.PostCheckAudit

def step_postcheck(session: Session, contracts: Contracts):
    states = [State.Discover, State.Validate, State.Sync, State.Arm, State.Deliver, State.Cooldown, State.PostCheckAudit]
    missing_all = []
    for st in states:
        missing = _check_tac(session, contracts, st)
        if missing:
            missing_all.append({"state": st.value, "missing": missing})

    ok = (len(missing_all) == 0)
    final = session.outcome or ("success" if ok and not session.blocked else "blocked")
    if not ok and final == "success":
        final = "blocked"

    emit(session, "postcheck_outcome", {"ok": ok, "missing": missing_all, "final": final})
    session.outcome = final
    session.state = State.PostCheckAudit
