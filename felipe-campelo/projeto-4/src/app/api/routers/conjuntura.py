from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.conjuntura import (
    CanonicalDocumentResponse,
    CanonicalMetricCutResponse,
    CanonicalMetricResponse,
    ConjunturaMetaResponse,
    ConjunturaQueryResponse,
    ConjunturaResponse,
    CoverageResponse,
    EvidenceResponse,
    ReferencePeriodResponse,
)
from app.repositories.query_repository import QueryRepository

router = APIRouter(prefix="/api/conjuntura", tags=["conjuntura"])


@router.get("", response_model=ConjunturaResponse)
def get_conjuntura(
    empresa: str = Query(...),
    ano: int = Query(..., ge=1900, le=9999),
    trimestre: int = Query(..., ge=1, le=4),
    metrica: str | None = Query(default=None),
    dimensao_recorte: str | None = Query(default=None),
    valor_recorte: str | None = Query(default=None),
    session: Session = Depends(get_database_session),
) -> ConjunturaResponse:
    repository = QueryRepository(session)
    company = repository.resolve_company(empresa)
    if company is None:
        raise HTTPException(status_code=404, detail="unknown_company")

    metric_catalog_item = None
    if metrica:
        metric_catalog_item = repository.resolve_metric_catalog_item(metrica)
        if metric_catalog_item is None:
            raise HTTPException(status_code=404, detail="unknown_metric")

    metrics = repository.list_canonical_metrics(
        company_id=company.id,
        year=ano,
        quarter=trimestre,
        metric_catalog_item_id=metric_catalog_item.id if metric_catalog_item else None,
    )
    document = repository.get_canonical_document_for_scope(company_id=company.id, year=ano, quarter=trimestre)

    filtered_data: list[CanonicalMetricResponse] = []
    for metric in metrics:
        cuts = repository.list_metric_cuts(metric.id)
        if dimensao_recorte is not None and not any(cut.dimension == dimensao_recorte for cut in cuts):
            continue
        if valor_recorte is not None and not any(cut.value == valor_recorte for cut in cuts):
            continue
        filtered_data.append(
            CanonicalMetricResponse(
                metric_slug=metric.metric_catalog_item.slug,
                metric_name=metric.metric_catalog_item.name,
                value=metric.value,
                value_status=metric.value_status,
                canonical_unit=metric.canonical_unit,
                reported_unit=metric.reported_unit,
                reported_value=metric.reported_value,
                cuts=[
                    CanonicalMetricCutResponse(dimension=cut.dimension, value=cut.value)
                    for cut in cuts
                ],
                evidence=EvidenceResponse(page=None, section=None, snippet=None),
            )
        )

    coverage = CoverageResponse(
        status="available" if document is not None else "unavailable",
        company_slug=company.slug,
        reference_period=ReferencePeriodResponse(year=ano, quarter=trimestre),
        canonical_document=(
            CanonicalDocumentResponse(
                document_id=f"doc_{document.id}",
                document_type=document.document_type,
                source_url=document.source_url,
                published_at=document.published_at,
            )
            if document is not None
            else None
        ),
        reason=None if document is not None else "no_canonical_document",
    )

    return ConjunturaResponse(
        query=ConjunturaQueryResponse(
            empresa=company.slug,
            ano=ano,
            trimestre=trimestre,
            metrica=metrica,
            dimensao_recorte=dimensao_recorte,
            valor_recorte=valor_recorte,
        ),
        coverage=coverage,
        data=filtered_data,
        meta=ConjunturaMetaResponse(
            returned_metrics=len(filtered_data),
            generated_at=datetime.now(timezone.utc),
        ),
    )
