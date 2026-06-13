from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class FetchedDocument:
    source_url: str
    effective_url: str
    content: bytes
    content_type: str | None


class DocumentFetchError(RuntimeError):
    """Raised when a signal cannot be converted into recoverable document content."""


class DocumentFetcher:
    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch(self, url: str) -> FetchedDocument:
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        content = response.content
        if not content:
            raise DocumentFetchError("Empty document response")

        content_type = response.headers.get("content-type")
        if content_type and "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
            raise DocumentFetchError(f"Unsupported content type: {content_type}")

        return FetchedDocument(
            source_url=url,
            effective_url=str(response.url),
            content=content,
            content_type=content_type,
        )
