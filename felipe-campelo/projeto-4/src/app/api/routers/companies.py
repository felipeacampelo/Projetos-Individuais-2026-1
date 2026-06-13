from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.company import CompanyItemResponse, CompanyListResponse
from app.repositories.company_repository import CompanyRepository

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_companies(session: Session = Depends(get_database_session)) -> CompanyListResponse:
    companies = CompanyRepository(session).list_active()
    data = [
        CompanyItemResponse(
            slug=company.slug,
            display_name=company.display_name,
            aliases=[alias.alias for alias in company.aliases if alias.alias_type != "ticker"],
            tickers=[alias.alias.upper() for alias in company.aliases if alias.alias_type == "ticker"],
        )
        for company in companies
    ]
    return CompanyListResponse(data=data)
