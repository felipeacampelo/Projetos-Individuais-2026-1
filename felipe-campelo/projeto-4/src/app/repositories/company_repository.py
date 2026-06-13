from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Company


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
