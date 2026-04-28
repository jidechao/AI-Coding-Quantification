from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_trailers import metric_from_raw
from gitlab_client import GitLabClient


def changed_lines(stats: dict[str, Any] | None) -> int:
    if not stats:
        return 0
    return int(stats.get("additions", 0) or 0) + int(stats.get("deletions", 0) or 0)


def normalize_commit(project_id: str, commit: dict[str, Any], pr_id: str | None = None) -> dict[str, Any]:
    metric = metric_from_raw(
        {
            "sha": commit.get("id") or commit.get("short_id"),
            "message": commit.get("message", ""),
            "lines_changed": changed_lines(commit.get("stats")),
        }
    )
    return {
        "commit_sha": metric.sha,
        "pr_id": pr_id,
        "repo": project_id,
        "author": commit.get("author_name") or commit.get("committer_name") or "unknown",
        "authored_at": commit.get("authored_date") or commit.get("created_at"),
        "ai_authorship": metric.authorship,
        "ai_tool": metric.ai_tool,
        "ai_model": metric.ai_model,
        "human_edit_ratio": metric.human_edit_ratio,
        "lines_changed": metric.lines_changed,
        "ai_mode": metric.ai_mode,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


def pull(project_id: str, ref_name: str = "main") -> list[dict[str, Any]]:
    client = GitLabClient()
    path = f"/projects/{project_id}/repository/commits"
    commits = client.paginate(path, {"ref_name": ref_name, "with_stats": "true"})
    return [normalize_commit(project_id, commit) for commit in commits]


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull GitLab commit metrics.")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--ref-name", default="main")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = pull(args.project_id, args.ref_name)
    Path(args.output).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} commits to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
