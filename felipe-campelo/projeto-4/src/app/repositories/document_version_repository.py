from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import DocumentVersion, DocumentVersionGroup


class DocumentVersionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_document_version(self, result_document_id: int) -> DocumentVersion | None:
        stmt = select(DocumentVersion).where(DocumentVersion.result_document_id == result_document_id)
        return self.session.scalar(stmt)

    def get_or_create_group(
        self,
        *,
        company_id: int,
        reference_year: int,
        reference_quarter: int,
    ) -> DocumentVersionGroup:
        stmt = select(DocumentVersionGroup).where(
            DocumentVersionGroup.company_id == company_id,
            DocumentVersionGroup.reference_year == reference_year,
            DocumentVersionGroup.reference_quarter == reference_quarter,
        )
        group = self.session.scalar(stmt)
        if group is not None:
            return group

        group = DocumentVersionGroup(
            company_id=company_id,
            reference_year=reference_year,
            reference_quarter=reference_quarter,
        )
        self.session.add(group)
        self.session.flush()
        return group

    def ensure_document_version(
        self,
        *,
        result_document_id: int,
        company_id: int,
        reference_year: int,
        reference_quarter: int,
    ) -> DocumentVersion:
        existing = self.get_document_version(result_document_id)
        if existing is not None:
            return existing

        group = self.get_or_create_group(
            company_id=company_id,
            reference_year=reference_year,
            reference_quarter=reference_quarter,
        )
        max_version = self.session.scalar(
            select(func.max(DocumentVersion.version_number)).where(
                DocumentVersion.version_group_id == group.id
            )
        )
        version = DocumentVersion(
            version_group_id=group.id,
            result_document_id=result_document_id,
            version_number=(max_version or 0) + 1,
        )
        self.session.add(version)
        self.session.flush()
        return version
