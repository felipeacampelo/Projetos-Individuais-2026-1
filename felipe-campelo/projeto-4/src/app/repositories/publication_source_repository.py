from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import PublicationSource


class PublicationSourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(self, company_id: int | None = None) -> list[PublicationSource]:
        stmt = (
            select(PublicationSource)
            .where(PublicationSource.is_active.is_(True))
            .options(joinedload(PublicationSource.company))
            .order_by(PublicationSource.priority.asc(), PublicationSource.id.asc())
        )
        if company_id is not None:
            stmt = stmt.where(PublicationSource.company_id == company_id)
        return list(self.session.scalars(stmt))
