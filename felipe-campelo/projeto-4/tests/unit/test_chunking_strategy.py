from app.extraction.chunking.strategy import (
    CandidateChunkSelector,
    ChunkingStrategyDecider,
    ParsingStrategy,
)
from app.extraction.parsers.pdf_parser import ParsedDocument, ParsedPage


def test_choose_full_scan_for_short_document() -> None:
    parsed = ParsedDocument(
        page_count=2,
        total_char_count=1000,
        pages=[
            ParsedPage(page_number=1, text="vendas líquidas", char_count=15),
            ParsedPage(page_number=2, text="estoque", char_count=7),
        ],
    )
    assert ChunkingStrategyDecider().choose(parsed) == ParsingStrategy.FULL_SCAN


def test_choose_semantic_chunking_for_large_document() -> None:
    parsed = ParsedDocument(
        page_count=20,
        total_char_count=50000,
        pages=[ParsedPage(page_number=1, text="texto", char_count=5)],
    )
    assert ChunkingStrategyDecider().choose(parsed) == ParsingStrategy.SEMANTIC_CHUNKING


def test_candidate_selector_scores_keyword_pages() -> None:
    selector = CandidateChunkSelector()
    parsed = ParsedDocument(
        page_count=2,
        total_char_count=100,
        pages=[
            ParsedPage(page_number=1, text="texto genérico", char_count=13),
            ParsedPage(page_number=2, text="Vendas líquidas e VSO do trimestre", char_count=35),
        ],
    )
    plan = selector.build_plan(parsed, ParsingStrategy.SEMANTIC_CHUNKING)
    assert len(plan.candidate_chunks) == 1
    assert plan.candidate_chunks[0].page_number == 2
