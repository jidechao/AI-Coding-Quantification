from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any


VALID_AUTHORSHIP = {"ai-authored", "ai-assisted", "human"}
TRAILER_RE = re.compile(r"^(AI-[A-Za-z-]+|Human-Edit-Ratio|Audit-Status):\s*(.+?)\s*$")


@dataclass(frozen=True)
class CommitMetric:
    sha: str
    authorship: str
    ai_tool: str
    ai_model: str
    human_edit_ratio: float
    ai_mode: str
    audit_status: str
    lines_changed: int


def parse_trailers(message: str) -> dict[str, str]:
    trailers: dict[str, str] = {}
    for line in message.splitlines():
        match = TRAILER_RE.match(line.strip())
        if match:
            trailers[match.group(1)] = match.group(2)
    return trailers


def metric_from_raw(raw: dict[str, Any]) -> CommitMetric:
    trailers = parse_trailers(str(raw.get("message", "")))
    authorship = trailers.get("AI-Authorship", "human")
    if authorship not in VALID_AUTHORSHIP:
        authorship = "human"
    ratio = float(trailers.get("Human-Edit-Ratio", 100))
    return CommitMetric(
        sha=str(raw.get("sha", "")),
        authorship=authorship,
        ai_tool=trailers.get("AI-Tool", "none"),
        ai_model=trailers.get("AI-Model", "none"),
        human_edit_ratio=ratio / 100 if ratio > 1 else ratio,
        ai_mode=trailers.get("AI-Mode", "auto"),
        audit_status=trailers.get("Audit-Status", "pending"),
        lines_changed=int(raw.get("lines_changed", 0)),
    )


def weighted_authorship(commits: list[CommitMetric]) -> str:
    totals = {"ai-authored": 0, "ai-assisted": 0, "human": 0}
    for commit in commits:
        totals[commit.authorship] += max(commit.lines_changed, 0)
    total_lines = sum(totals.values()) or 1
    if totals["ai-authored"] / total_lines >= 0.7:
        return "ai-authored"
    if (totals["ai-authored"] + totals["ai-assisted"]) / total_lines >= 0.3:
        return "ai-assisted"
    return "human"


def git_commit_range(base_ref: str, head_ref: str) -> list[dict[str, Any]]:
    fmt = "%H%x00%B%x00END_COMMIT"
    output = subprocess.check_output(
        ["git", "log", "--format=" + fmt, f"{base_ref}..{head_ref}"],
        text=True,
        encoding="utf-8",
    )
    commits: list[dict[str, Any]] = []
    for chunk in output.split("\x00END_COMMIT"):
        chunk = chunk.strip("\n\x00")
        if not chunk:
            continue
        sha, _, message = chunk.partition("\x00")
        lines = subprocess.check_output(
            ["git", "show", "--numstat", "--format=", "--no-renames", sha],
            text=True,
            encoding="utf-8",
        )
        changed = 0
        for line in lines.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                for value in parts[:2]:
                    if value.isdigit():
                        changed += int(value)
        commits.append({"sha": sha, "message": message, "lines_changed": changed})
    return commits


def update_gitlab_label(label: str) -> None:
    import requests

    api = os.environ["CI_API_V4_URL"]
    project_id = os.environ["CI_PROJECT_ID"]
    mr_iid = os.environ["CI_MERGE_REQUEST_IID"]
    token = os.environ["GITLAB_TOKEN"]
    url = f"{api}/projects/{project_id}/merge_requests/{mr_iid}"
    response = requests.put(
        url,
        headers={"PRIVATE-TOKEN": token},
        data={"add_labels": label},
        timeout=20,
    )
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse AI trailers and label a GitLab merge request.")
    parser.add_argument("--commits-json", help="Fixture JSON with sha/message/lines_changed entries.")
    parser.add_argument("--base-ref", default=os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_SHA") or "origin/main")
    parser.add_argument("--head-ref", default=os.environ.get("CI_COMMIT_SHA") or "HEAD")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.commits_json:
        with open(args.commits_json, encoding="utf-8") as fh:
            raw_commits = json.load(fh)
    else:
        raw_commits = git_commit_range(args.base_ref, args.head_ref)

    commits = [metric_from_raw(raw) for raw in raw_commits]
    missing = [commit.sha for commit in commits if commit.ai_tool == "none" and commit.authorship != "human"]
    if missing:
        raise SystemExit(f"AI commits missing AI-Tool trailer: {', '.join(missing)}")

    label = f"ai-authorship::{weighted_authorship(commits)}"
    print(json.dumps({"label": label, "commits": [commit.__dict__ for commit in commits]}, ensure_ascii=False, indent=2))
    if not args.dry_run:
        update_gitlab_label(label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
