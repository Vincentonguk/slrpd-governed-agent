import os
import asyncio
from typing import Any, Dict, Optional

import httpx


def base_url() -> str:
    # força IPv4 local e respeita env var
    return (os.getenv("SLRPD_API_BASE_URL") or "http://127.0.0.1:8010").rstrip("/")


async def get_openapi(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get(f"{base_url()}/openapi.json")
    r.raise_for_status()
    return r.json()


def list_paths(openapi: Dict[str, Any]) -> list[str]:
    return sorted(list((openapi or {}).get("paths", {}).keys()))


async def post_json(client: httpx.AsyncClient, path: str, payload: Dict[str, Any]) -> httpx.Response:
    url = f"{base_url()}{path}"
    return await client.post(url, json=payload)


async def get_json(client: httpx.AsyncClient, path: str) -> httpx.Response:
    url = f"{base_url()}{path}"
    return await client.get(url)


def pick_session_id(obj: Any) -> Optional[str]:
    # tenta achar session_id em vários formatos
    if isinstance(obj, dict):
        for k in ["session_id", "id", "sessionId"]:
            if k in obj and isinstance(obj[k], str):
                return obj[k]
    return None


def pick_approval_id(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        for k in ["approval_id", "approvalId", "id"]:
            if k in obj and isinstance(obj[k], str) and "approval" in k.lower():
                return obj[k]
        # às vezes vem como {"approval": {"id": "..."}}
        if "approval" in obj and isinstance(obj["approval"], dict):
            inner = obj["approval"]
            for k in ["id", "approval_id", "approvalId"]:
                if k in inner and isinstance(inner[k], str):
                    return inner[k]
    return None


async def main():
    print(f"[orchestrator] base_url={base_url()}")

    timeout = httpx.Timeout(connect=3.0, read=15.0, write=15.0, pool=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 1) conectividade real
        r = await client.get(f"{base_url()}/docs")
        print(f"[check] GET /docs -> {r.status_code}")
        if r.status_code != 200:
            print(r.text)
            return

        openapi = await get_openapi(client)
        paths = list_paths(openapi)
        print("[check] API paths:")
        for p in paths:
            print("  ", p)

        # 2) criar sessão (tenta /session e depois /session/custom)
        session_id = None
        if "/session" in paths:
            resp = await post_json(client, "/session", {})
            print(f"[call] POST /session -> {resp.status_code}")
            if resp.headers.get("content-type", "").startswith("application/json"):
                data = resp.json()
                print(data)
                session_id = pick_session_id(data)

        if not session_id and "/session/custom" in paths:
            # payload mínimo "chute" — se der 422, a API vai dizer campos requeridos
            resp = await post_json(client, "/session/custom", {"destination_profile": "DP-DC-01"})
            print(f"[call] POST /session/custom -> {resp.status_code}")
            print(resp.text)
            if resp.headers.get("content-type", "").startswith("application/json"):
                data = resp.json()
                session_id = pick_session_id(data)

        if not session_id:
            print("[FAIL] Não consegui obter session_id. A API provavelmente exige payload específico no /session (422).")
            print("Abra http://127.0.0.1:8010/docs e veja o schema do POST /session e /session/custom.")
            return

        print(f"[OK] session_id={session_id}")

        # 3) ask
        if f"/session/{{session_id}}/ask" in paths:
            resp = await post_json(client, f"/session/{session_id}/ask", {"question": "status?"})
            print(f"[call] POST /session/{{id}}/ask -> {resp.status_code}")
            print(resp.text)

        # 4) propose_action (pode gerar approval_id)
        approval_id = None
        if f"/session/{{session_id}}/propose_action" in paths:
            resp = await post_json(client, f"/session/{session_id}/propose_action", {"intent": "demo"})
            print(f"[call] POST /session/{{id}}/propose_action -> {resp.status_code}")
            print(resp.text)
            if resp.headers.get("content-type", "").startswith("application/json"):
                approval_id = pick_approval_id(resp.json())

        # 5) approve (se tiver approval_id)
        if approval_id and "/approval/{approval_id}/approve" in paths:
            resp = await post_json(client, f"/approval/{approval_id}/approve", {"approved": True})
            print(f"[call] POST /approval/{{id}}/approve -> {resp.status_code}")
            print(resp.text)

        # 6) simulate out of envelope
        if f"/session/{{session_id}}/simulate_out_of_envelope" in paths:
            resp = await post_json(client, f"/session/{session_id}/simulate_out_of_envelope", {"power_norm": 9.9})
            print(f"[call] POST /session/{{id}}/simulate_out_of_envelope -> {resp.status_code}")
            print(resp.text)

        # 7) finish
        if f"/session/{{session_id}}/finish" in paths:
            resp = await post_json(client, f"/session/{session_id}/finish", {})
            print(f"[call] POST /session/{{id}}/finish -> {resp.status_code}")
            print(resp.text)

        # 8) audit
        if f"/session/{{session_id}}/audit" in paths:
            resp = await get_json(client, f"/session/{session_id}/audit")
            print(f"[call] GET /session/{{id}}/audit -> {resp.status_code}")
            print(resp.text)

        print("\n[DONE] Orchestrator finalizado.")


if __name__ == "__main__":
    asyncio.run(main())
