from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories.publication_source_repository import PublicationSourceRepository


@dataclass(frozen=True)
class SourceRegistryItem:
    source_id: int
    company_id: int
    name: str
    source_type: str
    url: str
    priority: int


class SourceRegistry:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PublicationSourceRepository(session)

    def list_active_sources(self, company_id: int | None = None) -> list[SourceRegistryItem]:
        sources = self.repository.list_active(company_id=company_id)
        return [
            SourceRegistryItem(
                source_id=source.id,
                company_id=source.company_id,
                name=source.name,
                source_type=source.source_type,
                url=source.url,
                priority=source.priority,
            )
            for source in sources
        ]
