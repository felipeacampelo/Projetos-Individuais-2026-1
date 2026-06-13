from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.documents import (
    DocumentLineageResponse,
    DocumentLineageSignalResponse,
    DocumentItemResponse,
    DocumentListResponse,
    DocumentReferencePeriodResponse,
)
from app.repositories.query_repository import QueryRepository
from app.repositories.result_document_repository import ResultDocumentRepository

router = APIRouter(prefix="/api/documentos", tags=["documentos"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    empresa: str | None = Query(default=None),
    ano: int | None = Query(default=None),
    trimestre: int | None = Query(default=None),
    status: str | None = Query(default=None),
    canonical_only: bool = Query(default=False),
    session: Session = Depends(get_database_session),
) -> DocumentListResponse:
    repository = QueryRepository(session)
    company = repository.resolve_company(empresa) if empresa else None
    documents = repository.list_documents(
        company_id=company.id if company else None,
        status=status,
        canonical_only=canonical_only,
    )

    data = []
    for document in documents:
        version_group = document.version_entry.version_group if document.version_entry else None
        year = version_group.reference_year if version_group is not None else ano
        quarter = version_group.reference_quarter if version_group is not None else trimestre
        data.append(
            DocumentItemResponse(
                document_id=f"doc_{document.id}",
                company_slug=document.company.slug if document.company else None,
                reference_period=DocumentReferencePeriodResponse(year=year, quarter=quarter),
                version_number=document.version_entry.version_number if document.version_entry else None,
                document_type=document.document_type,
                status=document.current_state,
                source_url=document.source_url,
                content_hash=document.content_hash,
                published_at=document.published_at,
                is_canonical=document.current_state == "canonical",
            )
        )

    return DocumentListResponse(data=data)


@router.get("/{document_id}/linhagem", response_model=DocumentLineageResponse)
def get_document_lineage(
    document_id: int,
    session: Session = Depends(get_database_session),
) -> DocumentLineageResponse:
    document = ResultDocumentRepository(session).get_by_id_with_lineage(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="unknown_document")

    lineage_signals = []
    for link in document.discovery_links:
        signal = link.publication_signal
        lineage_signals.append(
            DocumentLineageSignalResponse(
                signal_id=f"signal_{signal.id}",
                publication_source_id=f"source_{signal.publication_source_id}",
                publication_source_name=(
                    signal.publication_source.name if signal.publication_source is not None else None
                ),
                signal_url=signal.signal_url,
                signal_title=signal.signal_title,
                discovered_at=signal.discovered_at,
                processing_status=signal.processing_status,
            )
        )

    return DocumentLineageResponse(
        document_id=f"doc_{document.id}",
        company_slug=document.company.slug if document.company else None,
        reference_period=(
            DocumentReferencePeriodResponse(
                year=document.version_entry.version_group.reference_year,
                quarter=document.version_entry.version_group.reference_quarter,
            )
            if document.version_entry is not None
            else None
        ),
        version_number=document.version_entry.version_number if document.version_entry else None,
        source_url=document.source_url,
        effective_url=document.effective_url,
        content_hash=document.content_hash,
        status=document.current_state,
        lineage_signals=lineage_signals,
    )
