from __future__ import annotations

import os
from typing import Any, Iterator


class GitLabClient:
    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("GITLAB_URL") or os.environ.get("CI_API_V4_URL") or "").rstrip("/")
        self.token = token or os.environ.get("GITLAB_TOKEN") or os.environ.get("PRIVATE_TOKEN") or ""
        if not self.base_url:
            raise ValueError("GITLAB_URL or CI_API_V4_URL is required")
        if "/api/v4" not in self.base_url:
            self.base_url = f"{self.base_url}/api/v4"

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        import requests

        response = requests.get(
            f"{self.base_url}{path}",
            headers={"PRIVATE-TOKEN": self.token} if self.token else {},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def paginate(self, path: str, params: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            data = self.get(path, {**(params or {}), "page": page, "per_page": 100})
            if not data:
                break
            yield from data
            page += 1
