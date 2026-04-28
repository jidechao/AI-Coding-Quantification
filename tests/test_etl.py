import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci" / "etl"))

from pull_commit import normalize_commit
from pull_mr import normalize_mr


class EtlTests(unittest.TestCase):
    def test_normalize_commit_extracts_trailers(self):
        row = normalize_commit(
            "group/project",
            {
                "id": "abc",
                "message": "x\n\nAI-Authorship: ai-assisted\nAI-Tool: cursor\nAI-Model: gpt\nHuman-Edit-Ratio: 50\nAI-Mode: auto\nAudit-Status: pending",
                "stats": {"additions": 3, "deletions": 2},
                "author_name": "dev",
                "authored_date": "2026-01-01T00:00:00Z",
            },
        )
        self.assertEqual(row["ai_authorship"], "ai-assisted")
        self.assertEqual(row["lines_changed"], 5)

    def test_normalize_mr_reads_ai_label(self):
        row = normalize_mr(
            "group/project",
            {
                "iid": 1,
                "labels": ["ai-authorship::ai-authored"],
                "author": {"username": "dev"},
                "state": "opened",
                "title": "Fixes #123 bug",
                "description": "",
            },
            changes=[{"diff": "@@ -1 +1 @@\n-old\n+new"}],
            commits=[
                {
                    "id": "abc",
                    "message": "x\n\nAI-Authorship: ai-authored\nAI-Tool: cursor\nAI-Model: gpt\nHuman-Edit-Ratio: 20\nAI-Mode: auto\nAudit-Status: pending",
                    "stats": {"additions": 1, "deletions": 1},
                }
            ],
            notes=[{"system": False, "author": {"username": "reviewer"}, "created_at": "2026-01-02T00:00:00Z"}],
        )
        self.assertEqual(row["ai_authorship"], "ai-authored")
        self.assertEqual(row["state"], "open")
        self.assertEqual(row["total_lines_added"], 1)
        self.assertEqual(row["total_lines_deleted"], 1)
        self.assertEqual(row["ai_lines"], 2)
        self.assertEqual(row["review_rounds"], 1)
        self.assertGreaterEqual(row["linked_bugs"], 1)


if __name__ == "__main__":
    unittest.main()
