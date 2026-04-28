from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "etl"))


@dataclass(frozen=True)
class AuditDecision:
    project_id: str
    mr_iid: str
    sampled: bool
    sample_rate: float
    sampled_at: str | None
    reason: str


@dataclass(frozen=True)
class AuditQueueRow:
    repo: str
    pr_id: str
    sampled_at: str
    status: str
    assignee: str | None
    reason: str


def deterministic_sample(project_id: str, mr_iid: str, sample_rate: float) -> bool:
    digest = hashlib.sha256(f"{project_id}:{mr_iid}".encode("utf-8")).hexdigest()
    value = int(digest[:8], 16) / 0xFFFFFFFF
    return value < sample_rate


def decide(project_id: str, mr_iid: str, sample_rate: float, enabled: bool = True) -> AuditDecision:
    if not enabled:
        return AuditDecision(project_id, mr_iid, False, sample_rate, None, "audit-disabled")
    sampled = deterministic_sample(project_id, mr_iid, sample_rate)
    return AuditDecision(
        project_id=project_id,
        mr_iid=mr_iid,
        sampled=sampled,
        sample_rate=sample_rate,
        sampled_at=datetime.now(timezone.utc).isoformat() if sampled else None,
        reason="sampled" if sampled else "not-sampled",
    )


def queue_row(decision: AuditDecision, assignee: str | None = None) -> AuditQueueRow | None:
    if not decision.sampled or not decision.sampled_at:
        return None
    return AuditQueueRow(
        repo=decision.project_id,
        pr_id=decision.mr_iid,
        sampled_at=decision.sampled_at,
        status="pending",
        assignee=assignee,
        reason=decision.reason,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically sample merge requests for AI metrics audit.")
    parser.add_argument("--project-id", default=os.environ.get("CI_PROJECT_ID", ""))
    parser.add_argument("--mr-iid", default=os.environ.get("CI_MERGE_REQUEST_IID", ""))
    parser.add_argument("--sample-rate", type=float, default=float(os.environ.get("AI_AUDIT_SAMPLE_RATE", "0.1")))
    parser.add_argument("--assignee", default=os.environ.get("AI_AUDIT_ASSIGNEE"))
    parser.add_argument("--disabled", action="store_true")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--queue-output", help="Optional audit_queue JSON path.")
    parser.add_argument("--load-mysql", action="store_true", help="Insert sampled rows into MySQL audit_queue.")
    args = parser.parse_args()

    result = decide(args.project_id, args.mr_iid, args.sample_rate, enabled=not args.disabled)
    payload = json.dumps(asdict(result), ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
    row = queue_row(result, args.assignee)
    rows = [asdict(row)] if row else []
    if args.queue_output:
        with open(args.queue_output, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    if args.load_mysql and rows:
        from load_mysql import connect, upsert_rows

        with connect() as connection:
            upsert_rows(connection, "audit_queue", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
