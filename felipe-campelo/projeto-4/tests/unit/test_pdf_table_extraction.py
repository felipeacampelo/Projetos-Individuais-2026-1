from app.extraction.chunking.strategy import ChunkingPlan, ParsingStrategy
from app.extraction.llm.heuristic import HeuristicExtractionClient
from app.extraction.parsers.pdf_parser import ParsedDocument, ParsedPage, ParsedTable
from app.extraction.pipelines.document_preparation import PreparedDocumentForExtraction


def _prepared_document(page: ParsedPage) -> PreparedDocumentForExtraction:
    parsed_document = ParsedDocument(page_count=1, pages=[page], total_char_count=page.char_count)
    return PreparedDocumentForExtraction(
        parsed_document=parsed_document,
        strategy=ParsingStrategy.FULL_SCAN,
        chunking_plan=ChunkingPlan(strategy=ParsingStrategy.FULL_SCAN, candidate_chunks=[]),
    )


def test_heuristic_extracts_facts_from_table_rows() -> None:
    page = ParsedPage(
        page_number=1,
        text="MRV 1T26 Prévia Operacional",
        char_count=28,
        tables=[
            ParsedTable(
                page_number=1,
                rows=[
                    ["Indicador", "1T26"],
                    ["VSO", "12,5%"],
                    ["Vendas Líquidas", "R$ 500 milhões"],
                ],
            )
        ],
    )

    contract = HeuristicExtractionClient().extract(
        prepared_document=_prepared_document(page),
        source_url="https://ri.example.com/mrv-1t26.pdf",
        document_type="previa_operacional",
    )

    facts_by_slug = {fact.reported_metric_name: fact for fact in contract.facts}
    assert facts_by_slug["vso"].reported_value == 12.5
    assert facts_by_slug["vso"].evidence.page == 1
    assert facts_by_slug["vendas-liquidas"].reported_value == 500.0
    assert facts_by_slug["vendas-liquidas"].reported_unit == "R$ milhões"


def test_table_row_takes_precedence_over_conflicting_free_text() -> None:
    page = ParsedPage(
        page_number=1,
        text="Comentario solto menciona VSO 99% em contexto de marketing",
        char_count=60,
        tables=[
            ParsedTable(
                page_number=1,
                rows=[["VSO", "12,5%"]],
            )
        ],
    )

    contract = HeuristicExtractionClient().extract(
        prepared_document=_prepared_document(page),
        source_url="https://ri.example.com/mrv-1t26.pdf",
        document_type="previa_operacional",
    )

    vso_facts = [fact for fact in contract.facts if fact.reported_metric_name == "vso"]
    assert len(vso_facts) == 1
    assert vso_facts[0].reported_value == 12.5
