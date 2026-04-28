from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_trailers import metric_from_raw
from gitlab_client import GitLabClient


def normalize_state(mr: dict[str, Any]) -> str:
    if mr.get("merged_at"):
        return "merged"
    state = mr.get("state", "open")
    return {"opened": "open", "closed": "closed", "merged": "merged"}.get(state, "open")


def diff_stats(changes: list[dict[str, Any]]) -> tuple[int, int]:
    added = 0
    deleted = 0
    for change in changes:
        for line in str(change.get("diff", "")).splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                deleted += 1
    return added, deleted


def linked_bug_count(mr: dict[str, Any]) -> int:
    text = f"{mr.get('title', '')}\n{mr.get('description', '')}".lower()
    patterns = [
        r"(?:fixes|closes|resolves)\s+#\d+",
        r"\bbug\b",
        r"\bdefect\b",
        r"缺陷",
        r"bugfix",
    ]
    return sum(len(re.findall(pattern, text)) for pattern in patterns)


def review_metrics(notes: list[dict[str, Any]], mr_author: str) -> tuple[int, str | None]:
    reviewer_notes = [
        note
        for note in notes
        if not note.get("system")
        and (note.get("author") or {}).get("username") != mr_author
        and note.get("created_at")
    ]
    first_review_at = min((note["created_at"] for note in reviewer_notes), default=None)
    review_days = {note["created_at"][:10] for note in reviewer_notes}
    return len(review_days), first_review_at


def commit_line_metrics(commits: list[dict[str, Any]]) -> tuple[int, int, int, str, str, str]:
    ai_lines = 0
    ai_assisted_lines = 0
    human_lines = 0
    tools: set[str] = set()
    models: set[str] = set()
    modes: set[str] = set()
    for commit in commits:
        stats = commit.get("stats") or {}
        lines_changed = int(stats.get("additions", 0) or 0) + int(stats.get("deletions", 0) or 0)
        metric = metric_from_raw(
            {
                "sha": commit.get("id") or commit.get("short_id"),
                "message": commit.get("message", ""),
                "lines_changed": lines_changed,
            }
        )
        tools.add(metric.ai_tool)
        models.add(metric.ai_model)
        modes.add(metric.ai_mode)
        if metric.authorship == "ai-authored":
            ai_lines += lines_changed
        elif metric.authorship == "ai-assisted":
            ai_assisted_lines += lines_changed
        else:
            human_lines += lines_changed
    return (
        ai_lines,
        ai_assisted_lines,
        human_lines,
        "mixed" if len(tools) > 1 else next(iter(tools), "none"),
        "mixed" if len(models) > 1 else next(iter(models), "none"),
        "mixed" if len(modes) > 1 else next(iter(modes), "auto"),
    )


def normalize_mr(
    project_id: str,
    mr: dict[str, Any],
    changes: list[dict[str, Any]] | None = None,
    commits: list[dict[str, Any]] | None = None,
    notes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    labels = mr.get("labels") or []
    ai_label = next((label.split("::", 1)[1] for label in labels if label.startswith("ai-authorship::")), "human")
    added, deleted = diff_stats(changes or [])
    ai_lines, ai_assisted_lines, human_lines, ai_tool, ai_model, ai_mode = commit_line_metrics(commits or [])
    review_rounds, first_review_at = review_metrics(notes or [], (mr.get("author") or {}).get("username", "unknown"))
    return {
        "pr_id": str(mr["iid"]),
        "repo": project_id,
        "author": (mr.get("author") or {}).get("username", "unknown"),
        "created_at": mr.get("created_at"),
        "merged_at": mr.get("merged_at"),
        "state": normalize_state(mr),
        "ai_authorship": ai_label,
        "ai_tool": ai_tool,
        "ai_model": ai_model,
        "total_lines_added": added,
        "total_lines_deleted": deleted,
        "ai_lines": ai_lines,
        "ai_assisted_lines": ai_assisted_lines,
        "human_lines": human_lines,
        "review_rounds": review_rounds,
        "first_review_at": first_review_at,
        "reverted": False,
        "reverted_at": None,
        "linked_bugs": linked_bug_count(mr),
        "ai_mode": ai_mode if ai_mode in {"auto", "manual", "hybrid"} else "auto",
        "audit_status": "pending",
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


def pull(project_id: str, state: str = "merged") -> list[dict[str, Any]]:
    client = GitLabClient()
    path = f"/projects/{project_id}/merge_requests"
    rows: list[dict[str, Any]] = []
    for mr in client.paginate(path, {"state": state}):
        iid = mr["iid"]
        changes_payload = client.get(f"/projects/{project_id}/merge_requests/{iid}/changes")
        commits = list(client.paginate(f"/projects/{project_id}/merge_requests/{iid}/commits"))
        notes = list(client.paginate(f"/projects/{project_id}/merge_requests/{iid}/notes"))
        rows.append(
            normalize_mr(
                project_id,
                mr,
                changes=changes_payload.get("changes", []),
                commits=commits,
                notes=notes,
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull GitLab merge request metrics.")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state", default="merged")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = pull(args.project_id, args.state)
    Path(args.output).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} merge requests to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
