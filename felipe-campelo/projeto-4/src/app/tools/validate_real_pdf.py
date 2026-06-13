from __future__ import annotations

import argparse
import json

from app.extraction.llm.heuristic import HeuristicExtractionClient
from app.extraction.pipelines.document_preparation import DocumentPreparationPipeline
from app.ingestion.fetchers.document_fetcher import DocumentFetcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a real PDF URL and run the heuristic semantic extraction contract."
    )
    parser.add_argument("--url", required=True, help="Official PDF URL to validate")
    parser.add_argument(
        "--document-type",
        default="documento_resultado",
        help="Document type used in the semantic contract",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    fetched = DocumentFetcher().fetch(args.url)
    prepared = DocumentPreparationPipeline().prepare(fetched.content)
    contract = HeuristicExtractionClient().extract(
        prepared_document=prepared,
        source_url=fetched.effective_url,
        document_type=args.document_type,
    )
    print(json.dumps(contract.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
