from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "authorship": {
        "mode": "auto",
        "default_tool": "cursor",
        "default_model": "none",
    },
    "heuristic": {
        "weights": {
            "commit_message_keywords": 0.4,
            "diff_volume": 0.3,
            "stylometry": 0.3,
        },
        "thresholds": {
            "ai_authored": 0.7,
            "ai_assisted": 0.3,
        },
        "diff_volume": {
            "small_lines": 30,
            "large_lines": 200,
        },
        "keyword_markers": [
            "ai",
            "agent",
            "cursor",
            "copilot",
            "claude",
            "generated",
            "draft",
        ],
    },
    "audit": {
        "enabled": True,
        "sample_rate": 0.1,
        "minimum_samples_per_week": 10,
    },
}


@dataclass(frozen=True)
class TrailerDefaults:
    authorship: str
    tool: str
    model: str
    ratio: int
    mode: str
    audit_status: str = "pending"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def parse_scalar(raw: str) -> Any:
    value = raw.strip().strip('"').strip("'")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small YAML subset used by .ai-coding-config.yml without dependencies."""
    if not path.exists():
        return {}
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any] | list[Any]]] = [(-1, root)]
    last_key_by_indent: dict[int, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            value = parse_scalar(line[2:])
            if isinstance(parent, list):
                parent.append(value)
            continue
        key, _, raw_value = line.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            if isinstance(parent, dict):
                parent[key] = parse_scalar(raw_value.split(" #", 1)[0])
        else:
            child: dict[str, Any] | list[Any] = [] if key in {"keyword_markers"} else {}
            if isinstance(parent, dict):
                parent[key] = child
            stack.append((indent, child))
            last_key_by_indent[indent] = key
            continue

    return root


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / ".ai-coding-config.yml").exists():
            return candidate
    return current


def load_config(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or find_repo_root()
    config = parse_simple_yaml(root / ".ai-coding-config.yml")
    return deep_merge(DEFAULT_CONFIG, config)


def trailer_defaults(config: dict[str, Any]) -> TrailerDefaults:
    mode = str(config["authorship"].get("mode", "auto"))
    if mode not in {"auto", "manual", "hybrid"}:
        mode = "auto"
    default_authorship = "ai-assisted" if mode != "manual" else "choose"
    default_ratio = 50 if default_authorship == "ai-assisted" else 100
    return TrailerDefaults(
        authorship=default_authorship,
        tool=str(config["authorship"].get("default_tool", "cursor")),
        model=str(config["authorship"].get("default_model", "none")),
        ratio=default_ratio,
        mode=mode,
    )
