from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]


def request(session: requests.Session, method: str, base_url: str, path: str, **kwargs: Any) -> Any:
    response = session.request(method, f"{base_url.rstrip('/')}{path}", timeout=30, **kwargs)
    response.raise_for_status()
    if response.text:
        return response.json()
    return None


def login(base_url: str, username: str, password: str) -> requests.Session:
    session = requests.Session()
    payload = request(
        session,
        "POST",
        base_url,
        "/api/session",
        json={"username": username, "password": password},
    )
    session.headers.update({"X-Metabase-Session": payload["id"]})
    return session


def find_database_id(session: requests.Session, base_url: str, database_name: str) -> int:
    payload = request(session, "GET", base_url, "/api/database")
    for database in payload.get("data", []):
        if database.get("name") == database_name:
            return int(database["id"])
    raise ValueError(f"Metabase database not found: {database_name}")


def create_card(session: requests.Session, base_url: str, database_id: int, spec: dict[str, Any]) -> int:
    sql = (ROOT / spec["query_file"]).read_text(encoding="utf-8")
    card = request(
        session,
        "POST",
        base_url,
        "/api/card",
        json={
            "name": spec["name"],
            "display": "table" if spec.get("visualization") == "table" else "line",
            "dataset_query": {
                "type": "native",
                "native": {"query": sql},
                "database": database_id,
            },
            "visualization_settings": {},
        },
    )
    return int(card["id"])


def create_dashboard(session: requests.Session, base_url: str, spec_path: Path, database_id: int) -> int:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    dashboard = request(
        session,
        "POST",
        base_url,
        "/api/dashboard",
        json={"name": spec["name"], "description": spec.get("description", "")},
    )
    dashboard_id = int(dashboard["id"])
    for index, card_spec in enumerate(spec.get("cards", [])):
        card_id = create_card(session, base_url, database_id, card_spec)
        request(
            session,
            "POST",
            base_url,
            f"/api/dashboard/{dashboard_id}/cards",
            json={
                "cardId": card_id,
                "row": (index // 2) * 8,
                "col": (index % 2) * 12,
                "sizeX": 12,
                "sizeY": 8,
            },
        )
    return dashboard_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Metabase cards and dashboards from dashboard specs.")
    parser.add_argument("--base-url", default=os.environ.get("METABASE_URL", "http://localhost:3000"))
    parser.add_argument("--username", default=os.environ.get("METABASE_USER"))
    parser.add_argument("--password", default=os.environ.get("METABASE_PASSWORD"))
    parser.add_argument("--database-name", default=os.environ.get("METABASE_DATABASE", "ai_metrics"))
    parser.add_argument("--spec-dir", default=str(Path(__file__).resolve().parent / "dashboards"))
    args = parser.parse_args()

    if not args.username or not args.password:
        raise SystemExit("METABASE_USER and METABASE_PASSWORD are required")

    session = login(args.base_url, args.username, args.password)
    database_id = find_database_id(session, args.base_url, args.database_name)
    created = []
    for spec_path in sorted(Path(args.spec_dir).glob("*.json")):
        created.append({"spec": str(spec_path), "dashboard_id": create_dashboard(session, args.base_url, spec_path, database_id)})
    print(json.dumps(created, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
