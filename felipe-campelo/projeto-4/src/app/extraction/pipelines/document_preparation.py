from __future__ import annotations

from dataclasses import dataclass

from app.extraction.chunking.strategy import (
    CandidateChunkSelector,
    ChunkingPlan,
    ChunkingStrategyDecider,
    ParsingStrategy,
)
from app.extraction.parsers.pdf_parser import ParsedDocument, PdfParser


@dataclass(frozen=True)
class PreparedDocumentForExtraction:
    parsed_document: ParsedDocument
    strategy: ParsingStrategy
    chunking_plan: ChunkingPlan


class DocumentPreparationPipeline:
    def __init__(
        self,
        parser: PdfParser | None = None,
        strategy_decider: ChunkingStrategyDecider | None = None,
        candidate_selector: CandidateChunkSelector | None = None,
    ) -> None:
        self.parser = parser or PdfParser()
        self.strategy_decider = strategy_decider or ChunkingStrategyDecider()
        self.candidate_selector = candidate_selector or CandidateChunkSelector()

    def prepare(self, content: bytes) -> PreparedDocumentForExtraction:
        parsed_document = self.parser.parse(content)
        strategy = self.strategy_decider.choose(parsed_document)
        chunking_plan = self.candidate_selector.build_plan(parsed_document, strategy)
        return PreparedDocumentForExtraction(
            parsed_document=parsed_document,
            strategy=strategy,
            chunking_plan=chunking_plan,
        )
