from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DiscoveredSignal:
    signal_url: str
    signal_title: str | None


def discover_pdf_signals_from_html(html: str, base_url: str) -> list[DiscoveredSignal]:
    soup = BeautifulSoup(html, "html.parser")
    discovered: list[DiscoveredSignal] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if ".pdf" not in href.lower():
            continue
        absolute_url = urljoin(base_url, href)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)
        title = " ".join(link.get_text(" ", strip=True).split()) or None
        discovered.append(
            DiscoveredSignal(
                signal_url=absolute_url,
                signal_title=title,
            )
        )

    return discovered
