from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.documents import (
    DocumentItemResponse,
    DocumentListResponse,
    DocumentReferencePeriodResponse,
)
from app.repositories.query_repository import QueryRepository

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
        year = ano if ano is not None else None
        quarter = trimestre if trimestre is not None else None
        data.append(
            DocumentItemResponse(
                document_id=f"doc_{document.id}",
                company_slug=document.company.slug if document.company else None,
                reference_period=DocumentReferencePeriodResponse(year=year, quarter=quarter),
                document_type=document.document_type,
                status=document.current_state,
                source_url=document.source_url,
                content_hash=document.content_hash,
                published_at=document.published_at,
                is_canonical=document.current_state == "canonical",
            )
        )

    return DocumentListResponse(data=data)
