import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "githooks" / "lib"))

from config import load_config, parse_simple_yaml, trailer_defaults


class ConfigTests(unittest.TestCase):
    def test_parse_simple_yaml_lists_and_nested_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".ai-coding-config.yml"
            path.write_text(
                """
authorship:
  mode: hybrid
heuristic:
  keyword_markers:
    - cursor
    - claude
audit:
  sample_rate: 0.2
""".strip(),
                encoding="utf-8",
            )
            parsed = parse_simple_yaml(path)
            self.assertEqual(parsed["authorship"]["mode"], "hybrid")
            self.assertEqual(parsed["heuristic"]["keyword_markers"], ["cursor", "claude"])
            self.assertEqual(parsed["audit"]["sample_rate"], 0.2)

    def test_defaults_follow_mode(self):
        config = load_config(ROOT)
        defaults = trailer_defaults(config)
        self.assertIn(defaults.mode, {"auto", "manual", "hybrid"})


if __name__ == "__main__":
    unittest.main()
