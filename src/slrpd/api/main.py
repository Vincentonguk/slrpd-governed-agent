import os
from fastapi import FastAPI, HTTPException
from typing import Dict, Optional, List

from ..config import settings
from ..state_machine.policies import load_contracts
from ..state_machine.transitions import (
    Session, step_discover, step_validate, step_sync, step_arm,
    step_deliver, step_cooldown, step_postcheck
)
from ..rag.index import SimpleCorpusIndex
from ..rag.retrieve import rag_answer
from ..observability.audit_log import read_events
from ..observability.events import AuditEvent
from ..observability.audit_log import append_event
from ..execution.approvals import ApprovalRequest
from ..execution.tools import run_tool

from .schemas import AskRequest, AskResponse, ProposeActionRequest, ApproveRequest

app = FastAPI(title="SLRPD Governed Agent", version="0.1.0")

SESSIONS: Dict[str, Session] = {}
APPROVALS: Dict[str, ApprovalRequest] = {}

CONTRACTS = load_contracts()

INDEX = SimpleCorpusIndex()
def _load_index():
    os.makedirs(settings.corpus_dir, exist_ok=True)
    INDEX.load_from_dir(settings.corpus_dir)
_load_index()

def _ensure_session(session_id: str) -> Session:
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session_not_found")
    return s

@app.post("/session")
def create_session():
    return create_session_custom(destination_id="DC-DEST-001")

@app.post("/session/custom")
def create_session_custom(destination_id: Optional[str] = None):
    s = Session()
    SESSIONS[s.id] = s

    step_discover(s, destination_id=destination_id)
    ok = step_validate(s, CONTRACTS)

    if ok and s.state.value == "Sync":
        step_sync(s)
    if ok:
        step_arm(s, CONTRACTS)

    return {"session_id": s.id, "state": s.state.value, "outcome": s.outcome, "destination_id": s.destination_id}

@app.post("/session/{session_id}/faults")
def set_faults(session_id: str, drop_event_types: List[str]):
    s = _ensure_session(session_id)
    s.drop_event_types = set(drop_event_types)
    return {"session_id": s.id, "drop_event_types": list(s.drop_event_types)}

@app.post("/session/{session_id}/ask", response_model=AskResponse)
def ask(session_id: str, req: AskRequest):
    s = _ensure_session(session_id)
    if s.state.value != "Deliver":
        raise HTTPException(status_code=409, detail=f"session_not_in_deliver:{s.state.value}")

    min_score = float(CONTRACTS.dp.get("tolerances", {}).get("min_retrieval_score", settings.min_retrieval_score_default))
    out = rag_answer(INDEX, req.question, min_score=min_score)

    append_event(AuditEvent(session_id=s.id, event_type="rag_query", state=s.state.value, data={
        "question": req.question,
        "ok": out["ok"],
        "reason": out["reason"],
        "min_score": min_score
    }))

    if not out["ok"]:
        s.deferred_queries.append({"q": req.question, "reason": out["reason"]})
        return AskResponse(ok=False, answer=None, citations=out["citations"], reason=out["reason"], state=s.state.value)

    return AskResponse(ok=True, answer=out["answer"], citations=out["citations"], reason=out["reason"], state=s.state.value)

@app.post("/session/{session_id}/propose_action")
def propose_action(session_id: str, req: ProposeActionRequest):
    s = _ensure_session(session_id)
    if s.state.value != "Deliver":
        raise HTTPException(status_code=409, detail=f"session_not_in_deliver:{s.state.value}")

    allowed = set(CONTRACTS.se.get("limits", {}).get("allowed_tools", []))
    if req.action not in allowed:
        append_event(AuditEvent(session_id=s.id, event_type="action_blocked", state=s.state.value, data={
            "action": req.action, "reason": "not_in_allowlist"
        }))
        raise HTTPException(status_code=403, detail="action_not_allowed_by_policy")

    if s.actions_count >= int(CONTRACTS.se.get("limits", {}).get("max_actions_per_session", 3)):
        raise HTTPException(status_code=429, detail="max_actions_per_session_exceeded")

    ar = ApprovalRequest(session_id=s.id, action=req.action, payload=req.payload)
    APPROVALS[ar.id] = ar

    append_event(AuditEvent(session_id=s.id, event_type="approval_requested", state=s.state.value, data={
        "approval_id": ar.id, "action": ar.action, "payload": ar.payload
    }))
    return {"approval_id": ar.id, "status": ar.status}

@app.post("/approval/{approval_id}/approve")
def approve_action(approval_id: str, req: ApproveRequest):
    ar = APPROVALS.get(approval_id)
    if not ar:
        raise HTTPException(status_code=404, detail="approval_not_found")
    if ar.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval_not_pending:{ar.status}")

    s = _ensure_session(ar.session_id)

    ar.status = "approved"
    ar.approver = req.approver
    s.actions_count += 1

    append_event(AuditEvent(session_id=s.id, event_type="approval_granted", state=s.state.value, data={
        "approval_id": ar.id, "approver": req.approver
    }))

    result = run_tool(ar.action, ar.payload)

    append_event(AuditEvent(session_id=s.id, event_type="action_executed", state=s.state.value, data={
        "approval_id": ar.id, "tool_result": result
    }))

    return {"approval_id": ar.id, "status": ar.status, "result": result}

@app.post("/session/{session_id}/finish")
def finish(session_id: str):
    s = _ensure_session(session_id)
    if s.state.value != "Deliver":
        raise HTTPException(status_code=409, detail=f"session_not_in_deliver:{s.state.value}")

    step_deliver(s, in_envelope=True)
    step_cooldown(s)
    step_postcheck(s, CONTRACTS)
    return {"session_id": s.id, "state": s.state.value, "outcome": s.outcome}

@app.post("/session/{session_id}/simulate_out_of_envelope")
def simulate_out_of_envelope(session_id: str):
    s = _ensure_session(session_id)
    if s.state.value != "Deliver":
        raise HTTPException(status_code=409, detail=f"session_not_in_deliver:{s.state.value}")

    step_deliver(s, in_envelope=False)
    step_cooldown(s)
    step_postcheck(s, CONTRACTS)
    return {"session_id": s.id, "state": s.state.value, "outcome": s.outcome}

@app.get("/session/{session_id}/audit")
def audit(session_id: str):
    s = _ensure_session(session_id)
    return {
        "session_id": s.id,
        "state": s.state.value,
        "outcome": s.outcome,
        "destination_id": s.destination_id,
        "deferred_queries": s.deferred_queries,
        "events": read_events(s.id)
    }
