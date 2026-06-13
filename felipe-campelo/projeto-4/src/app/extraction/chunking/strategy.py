from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.extraction.parsers.pdf_parser import ParsedDocument, ParsedPage


class ParsingStrategy(StrEnum):
    FULL_SCAN = "full_scan"
    SEMANTIC_CHUNKING = "semantic_chunking"


KEYWORD_PRIORITIES = [
    "vendas",
    "vendas líquidas",
    "vso",
    "lançamentos",
    "estoque",
    "unidades",
    "repasses",
    "banco de terrenos",
    "landbank",
]


@dataclass(frozen=True)
class CandidateChunk:
    page_number: int
    score: int
    text: str
    matched_keywords: list[str]


@dataclass(frozen=True)
class ChunkingPlan:
    strategy: ParsingStrategy
    candidate_chunks: list[CandidateChunk]


class ChunkingStrategyDecider:
    def __init__(self, max_full_scan_pages: int = 8, max_full_scan_chars: int = 16000) -> None:
        self.max_full_scan_pages = max_full_scan_pages
        self.max_full_scan_chars = max_full_scan_chars

    def choose(self, parsed_document: ParsedDocument) -> ParsingStrategy:
        if (
            parsed_document.page_count <= self.max_full_scan_pages
            and parsed_document.total_char_count <= self.max_full_scan_chars
        ):
            return ParsingStrategy.FULL_SCAN
        return ParsingStrategy.SEMANTIC_CHUNKING


class CandidateChunkSelector:
    def __init__(self, keywords: list[str] | None = None) -> None:
        self.keywords = keywords or KEYWORD_PRIORITIES

    def score_page(self, page: ParsedPage) -> CandidateChunk:
        lowered = page.text.lower()
        matched_keywords = [keyword for keyword in self.keywords if keyword in lowered]
        score = len(matched_keywords)
        return CandidateChunk(
            page_number=page.page_number,
            score=score,
            text=page.text,
            matched_keywords=matched_keywords,
        )

    def build_plan(self, parsed_document: ParsedDocument, strategy: ParsingStrategy) -> ChunkingPlan:
        if strategy == ParsingStrategy.FULL_SCAN:
            chunks = [
                CandidateChunk(
                    page_number=page.page_number,
                    score=0,
                    text=page.text,
                    matched_keywords=[],
                )
                for page in parsed_document.pages
            ]
            return ChunkingPlan(strategy=strategy, candidate_chunks=chunks)

        scored = [self.score_page(page) for page in parsed_document.pages]
        filtered = [chunk for chunk in scored if chunk.score > 0]
        ranked = sorted(filtered, key=lambda item: (-item.score, item.page_number))
        return ChunkingPlan(strategy=strategy, candidate_chunks=ranked)
