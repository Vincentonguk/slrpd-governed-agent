import os, json, hashlib
from typing import List
from .events import AuditEvent
from ..config import settings

def _ensure_dirs():
    os.makedirs(settings.audit_dir, exist_ok=True)

def _hash_event(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def append_event(ev: AuditEvent) -> AuditEvent:
    _ensure_dirs()
    payload = ev.model_dump()
    payload["integrity_hash"] = _hash_event({k: v for k, v in payload.items() if k != "integrity_hash"})
    ev.integrity_hash = payload["integrity_hash"]

    path = os.path.join(settings.audit_dir, f"{ev.session_id}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    return ev

def read_events(session_id: str) -> List[dict]:
    path = os.path.join(settings.audit_dir, f"{session_id}.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
