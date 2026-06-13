from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.reprocessing import (
    ReprocessingRequestDetailResponse,
    ReprocessingRequestItemResponse,
    ReprocessingRequestListResponse,
)
from app.repositories.reprocessing_repository import ReprocessingRepository

router = APIRouter(prefix="/api/reprocessamentos", tags=["reprocessamentos"])


@router.get("", response_model=ReprocessingRequestListResponse)
def list_reprocessing_requests(session: Session = Depends(get_database_session)) -> ReprocessingRequestListResponse:
    requests = ReprocessingRepository(session).list_requests()
    return ReprocessingRequestListResponse(
        data=[
            ReprocessingRequestItemResponse(
                request_id=f"reprocess_{request.id}",
                document_id=f"doc_{request.result_document_id}",
                company_slug=(
                    request.result_document.company.slug
                    if request.result_document is not None and request.result_document.company is not None
                    else None
                ),
                trigger_type=request.trigger_type,
                trigger_version=request.trigger_version,
                status=request.status,
                created_at=request.created_at,
                started_at=request.started_at,
                finished_at=request.finished_at,
                error_message=request.error_message,
            )
            for request in requests
        ]
    )


@router.get("/{request_id}", response_model=ReprocessingRequestDetailResponse)
def get_reprocessing_request(
    request_id: int,
    session: Session = Depends(get_database_session),
) -> ReprocessingRequestDetailResponse:
    request = ReprocessingRepository(session).get_request(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="unknown_reprocessing_request")

    document = request.result_document
    return ReprocessingRequestDetailResponse(
        request_id=f"reprocess_{request.id}",
        document_id=f"doc_{request.result_document_id}",
        company_slug=(
            document.company.slug if document is not None and document.company is not None else None
        ),
        trigger_type=request.trigger_type,
        trigger_version=request.trigger_version,
        status=request.status,
        created_at=request.created_at,
        started_at=request.started_at,
        finished_at=request.finished_at,
        error_message=request.error_message,
        source_url=document.source_url if document is not None else None,
        effective_url=document.effective_url if document is not None else None,
        document_status=document.current_state if document is not None else None,
        contract_version_used=document.contract_version_used if document is not None else None,
        normalization_version_used=document.normalization_version_used if document is not None else None,
    )
