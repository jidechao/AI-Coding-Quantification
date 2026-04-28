import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci"))

from audit_sampler import deterministic_sample, decide, queue_row
from parse_trailers import metric_from_raw, weighted_authorship


class CiTests(unittest.TestCase):
    def test_weighted_authorship_prefers_ai_authored_lines(self):
        commits = [
            metric_from_raw(
                {
                    "sha": "a",
                    "lines_changed": 80,
                    "message": "x\n\nAI-Authorship: ai-authored\nAI-Tool: cursor\nAI-Model: gpt\nHuman-Edit-Ratio: 10\nAI-Mode: auto\nAudit-Status: pending",
                }
            ),
            metric_from_raw(
                {
                    "sha": "b",
                    "lines_changed": 20,
                    "message": "x\n\nAI-Authorship: human\nAI-Tool: none\nAI-Model: none\nHuman-Edit-Ratio: 100\nAI-Mode: manual\nAudit-Status: pending",
                }
            ),
        ]
        self.assertEqual(weighted_authorship(commits), "ai-authored")

    def test_audit_sampling_is_deterministic(self):
        self.assertEqual(
            deterministic_sample("1", "42", 0.2),
            deterministic_sample("1", "42", 0.2),
        )

    def test_audit_queue_row_matches_schema(self):
        decision = decide("group/project", "7", 1.0)
        row = queue_row(decision, assignee="auditor")
        self.assertIsNotNone(row)
        self.assertEqual(row.repo, "group/project")
        self.assertEqual(row.pr_id, "7")
        self.assertEqual(row.status, "pending")
        self.assertEqual(row.assignee, "auditor")


if __name__ == "__main__":
    unittest.main()
