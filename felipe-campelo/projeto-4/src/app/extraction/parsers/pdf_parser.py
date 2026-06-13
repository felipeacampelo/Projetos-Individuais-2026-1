from __future__ import annotations

from dataclasses import dataclass

import fitz


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str
    char_count: int


@dataclass(frozen=True)
class ParsedDocument:
    page_count: int
    pages: list[ParsedPage]
    total_char_count: int


class PdfParser:
    def parse(self, content: bytes) -> ParsedDocument:
        document = fitz.open(stream=content, filetype="pdf")
        pages: list[ParsedPage] = []

        try:
            for index, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                pages.append(
                    ParsedPage(
                        page_number=index,
                        text=text,
                        char_count=len(text),
                    )
                )
        finally:
            document.close()

        return ParsedDocument(
            page_count=len(pages),
            pages=pages,
            total_char_count=sum(page.char_count for page in pages),
        )
