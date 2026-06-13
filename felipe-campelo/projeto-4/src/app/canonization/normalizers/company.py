from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Company, CompanyAlias


class CompanyNormalizer:
    def __init__(self, session: Session) -> None:
        self.session = session

    def normalize(self, reported_name: str | None) -> Company | None:
        if not reported_name:
            return None
        normalized = reported_name.strip().lower()
        stmt = (
            select(Company)
            .outerjoin(CompanyAlias, CompanyAlias.company_id == Company.id)
            .where(
                Company.is_active.is_(True),
                or_(
                    func.lower(Company.slug) == normalized,
                    func.lower(Company.display_name) == normalized,
                    func.lower(CompanyAlias.alias) == normalized,
                ),
            )
            .limit(1)
        )
        return self.session.scalar(stmt)
