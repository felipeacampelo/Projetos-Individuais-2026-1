from __future__ import annotations

from dataclasses import dataclass, field

import fitz


@dataclass(frozen=True)
class ParsedTable:
    page_number: int
    rows: list[list[str]]


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str
    char_count: int
    tables: list[ParsedTable] = field(default_factory=list)


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
                        tables=self._extract_tables(page, page_number=index),
                    )
                )
        finally:
            document.close()

        return ParsedDocument(
            page_count=len(pages),
            pages=pages,
            total_char_count=sum(page.char_count for page in pages),
        )

    @staticmethod
    def _extract_tables(page: fitz.Page, *, page_number: int) -> list[ParsedTable]:
        tables: list[ParsedTable] = []
        for table in page.find_tables().tables:
            rows = [[(cell or "").strip() for cell in row] for row in table.extract()]
            rows = [row for row in rows if any(cell for cell in row)]
            if rows:
                tables.append(ParsedTable(page_number=page_number, rows=rows))
        return tables
