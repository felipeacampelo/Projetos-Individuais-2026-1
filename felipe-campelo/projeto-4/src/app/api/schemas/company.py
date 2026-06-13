from __future__ import annotations

from pydantic import BaseModel


class CompanyItemResponse(BaseModel):
    slug: str
    display_name: str
    aliases: list[str]
    tickers: list[str]


class CompanyListResponse(BaseModel):
    data: list[CompanyItemResponse]
