import os, json
from typing import Dict, Any
from ..config import settings

ALLOWED_TOOLS = {"create_report"}

def run_tool(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("tool_not_allowed")

    os.makedirs(settings.reports_dir, exist_ok=True)
    title = payload.get("title", "report")
    path = os.path.join(settings.reports_dir, f"{title.replace(' ', '_')}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"title": title, "payload": payload}, f, indent=2)

    return {"tool": tool_name, "report_path": path}
