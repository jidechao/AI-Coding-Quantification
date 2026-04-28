from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from config import load_config
from stylometry import score_diff


AUTHORSHIP_AI = "ai-authored"
AUTHORSHIP_ASSISTED = "ai-assisted"
AUTHORSHIP_HUMAN = "human"


@dataclass(frozen=True)
class Estimate:
    probability_ai: float
    authorship: str
    human_edit_ratio: int
    signals: dict[str, float]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def message_score(text: str, markers: list[str]) -> float:
    lower = text.lower()
    hits = 0
    for marker in markers:
        if re.search(rf"\b{re.escape(marker.lower())}\b", lower):
            hits += 1
    if "co-authored-by:" in lower and any(name in lower for name in ("claude", "copilot", "cursor", "ai")):
        hits += 2
    return clamp(hits / 3)


def diff_volume_score(text: str, small_lines: int, large_lines: int) -> float:
    changed = 0
    for line in text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            changed += 1
        elif line.startswith("-") and not line.startswith("---"):
            changed += 1
    if changed <= small_lines:
        return 0.0
    if changed >= large_lines:
        return 1.0
    return (changed - small_lines) / max(large_lines - small_lines, 1)


def classify(probability_ai: float, thresholds: dict[str, Any]) -> str:
    ai_authored = float(thresholds.get("ai_authored", 0.7))
    ai_assisted = float(thresholds.get("ai_assisted", 0.3))
    if probability_ai >= ai_authored:
        return AUTHORSHIP_AI
    if probability_ai >= ai_assisted:
        return AUTHORSHIP_ASSISTED
    return AUTHORSHIP_HUMAN


def estimate_from_text(text: str, config: dict[str, Any] | None = None) -> Estimate:
    cfg = config or load_config()
    heuristic = cfg["heuristic"]
    weights = heuristic["weights"]
    markers = [str(m) for m in heuristic.get("keyword_markers", [])]
    volume_cfg = heuristic.get("diff_volume", {})

    signals = {
        "commit_message_keywords": message_score(text, markers),
        "diff_volume": diff_volume_score(
            text,
            int(volume_cfg.get("small_lines", 30)),
            int(volume_cfg.get("large_lines", 200)),
        ),
        "stylometry": score_diff(text),
    }
    weighted = sum(float(weights.get(name, 0.0)) * value for name, value in signals.items())
    total_weight = sum(float(weights.get(name, 0.0)) for name in signals) or 1.0
    probability = clamp(weighted / total_weight)
    authorship = classify(probability, heuristic["thresholds"])
    ratio = int(round((1 - probability) * 100))
    if authorship == AUTHORSHIP_HUMAN:
        ratio = max(ratio, 70)
    elif authorship == AUTHORSHIP_AI:
        ratio = min(ratio, 30)
    return Estimate(probability, authorship, ratio, signals)


def trailer_output(estimate: Estimate) -> str:
    return "\n".join(
        [
            f"AI-Authorship: {estimate.authorship}",
            f"Human-Edit-Ratio: {estimate.human_edit_ratio}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate AI authorship from commit message and diff text.")
    parser.add_argument("path", nargs="?", help="File containing commit/diff text.")
    parser.add_argument("--stdin", action="store_true", help="Read commit/diff text from stdin.")
    parser.add_argument("--format", choices=("json", "trailer"), default="json")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.path:
        text = Path(args.path).read_text(encoding="utf-8")
    else:
        parser.error("provide --stdin or a path")

    estimate = estimate_from_text(text)
    if args.format == "trailer":
        print(trailer_output(estimate))
    else:
        print(json.dumps(asdict(estimate), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
