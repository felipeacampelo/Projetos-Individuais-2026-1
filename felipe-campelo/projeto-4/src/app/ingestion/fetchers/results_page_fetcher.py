from __future__ import annotations

import httpx


class ResultsPageFetchError(RuntimeError):
    """Raised when a publication source page cannot be fetched as HTML."""


class ResultsPageFetcher:
    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_html(self, url: str) -> str:
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower() and "<html" not in response.text.lower():
            raise ResultsPageFetchError(f"Unsupported results page content type: {content_type}")

        return response.text
