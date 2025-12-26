from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass(frozen=True)
class Contracts:
    dp: Dict[str, Any]
    se: Dict[str, Any]
    cs: Dict[str, Any]
    tac: Dict[str, Any]


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {path} (cwd={Path.cwd()})")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML root in {path}: expected mapping/dict")
    return data


def load_contracts(base_dir: str | None = None) -> Contracts:
    base = Path(base_dir) if base_dir else (Path.cwd() / "contracts")
    return Contracts(
        dp=_load_yaml(base / "dp.yaml"),
        se=_load_yaml(base / "se.yaml"),
        cs=_load_yaml(base / "cs.yaml"),
        tac=_load_yaml(base / "tac.yaml"),
    )


def tac_required_events(contracts: Contracts) -> List[str]:
    tac = (contracts.tac or {}).get("tac", {})
    events = tac.get("required_events", [])
    if not isinstance(events, list):
        return []
    return [str(e) for e in events]


def tac_required_fields(contracts: Contracts) -> List[str]:
    tac = (contracts.tac or {}).get("tac", {})
    fields = tac.get("required_fields", [])
    if not isinstance(fields, list):
        return []
    return [str(f) for f in fields]
