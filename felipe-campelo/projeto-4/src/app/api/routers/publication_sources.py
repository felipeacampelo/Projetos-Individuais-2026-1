from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.publication_sources import (
    PublicationSourceItemResponse,
    PublicationSourceListResponse,
)
from app.repositories.company_repository import CompanyRepository
from app.repositories.publication_source_repository import PublicationSourceRepository

router = APIRouter(prefix="/api/fontes-publicacao", tags=["fontes-publicacao"])


@router.get("", response_model=PublicationSourceListResponse)
def list_publication_sources(
    empresa: str | None = Query(default=None),
    session: Session = Depends(get_database_session),
) -> PublicationSourceListResponse:
    company = CompanyRepository(session).resolve_active(empresa) if empresa else None
    sources = PublicationSourceRepository(session).list_active(company_id=company.id if company else None)
    return PublicationSourceListResponse(
        data=[
            PublicationSourceItemResponse(
                source_id=f"source_{source.id}",
                company_slug=source.company.slug,
                name=source.name,
                source_type=source.source_type,
                url=source.url,
                priority=source.priority,
                is_active=source.is_active,
            )
            for source in sources
        ]
    )
