from pathlib import Path

base = Path("contracts")
base.mkdir(parents=True, exist_ok=True)

(base / "dp.yaml").write_text(
"""destination_profiles:
  DP-DC-01:
    destination_type: data_center
    version: "0.1"
    safe_envelope_ref: SE-DC-01
    sync_required: false
""",
encoding="utf-8",
)

(base / "se.yaml").write_text(
"""safe_envelopes:
  SE-DC-01:
    version: "0.1"
    max_power_norm: 1.0
    max_jitter_norm: 0.2
    max_latency_ms: 50
    deny_by_default: true
""",
encoding="utf-8",
)

(base / "cs.yaml").write_text(
"""capabilities:
  CS-SLRPD-01:
    version: "0.1"
    supports_closed_loop: true
    supports_cooldown: true
    supports_audit: true
""",
encoding="utf-8",
)

(base / "tac.yaml").write_text(
"""tac:
  version: "0.1"
  required_events:
    - Discover
    - Validate
    - Sync
    - Arm
    - Deliver
    - Cooldown
    - PostCheckAudit
  required_fields:
    - session_id
    - event_type
    - state
    - ts
""",
encoding="utf-8",
)

print("OK: contracts/*.yaml created")
