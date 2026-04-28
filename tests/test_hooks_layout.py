import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HookLayoutTests(unittest.TestCase):
    def test_required_hooks_exist(self):
        for name in ("install.sh", "prepare-commit-msg", "commit-msg", "post-commit"):
            self.assertTrue((ROOT / "githooks" / name).exists(), name)

    def test_trailer_contract_is_declared(self):
        trailer = (ROOT / "githooks" / "lib" / "trailer.sh").read_text(encoding="utf-8")
        for field in (
            "AI-Authorship",
            "AI-Tool",
            "AI-Model",
            "Human-Edit-Ratio",
            "AI-Mode",
            "Audit-Status",
        ):
            self.assertIn(field, trailer)


if __name__ == "__main__":
    unittest.main()
