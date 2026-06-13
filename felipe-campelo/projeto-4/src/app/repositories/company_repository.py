from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Company, CompanyAlias


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(self) -> list[Company]:
        stmt = (
            select(Company)
            .where(Company.is_active.is_(True))
            .options(selectinload(Company.aliases))
            .order_by(Company.slug.asc())
        )
        return list(self.session.scalars(stmt))

    def resolve_active(self, company_ref: str) -> Company | None:
        normalized = company_ref.strip().lower()
        stmt = (
            select(Company)
            .outerjoin(CompanyAlias, CompanyAlias.company_id == Company.id)
            .where(
                Company.is_active.is_(True),
                (Company.slug == normalized)
                | (Company.display_name.ilike(normalized))
                | (CompanyAlias.alias.ilike(normalized))
            )
            .options(selectinload(Company.aliases))
            .limit(1)
        )
        return self.session.scalar(stmt)
