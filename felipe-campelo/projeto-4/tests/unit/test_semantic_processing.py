from __future__ import annotations

import fitz
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Company, CompanyAlias, MetricCatalogAlias, MetricCatalogItem, ResultDocument
from app.domain.document_lifecycle import DocumentState
from app.extraction.service import DocumentSemanticProcessingService


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def build_pdf_bytes(text_lines: list[str]) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "\n".join(text_lines))
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def seed_company_and_metric_catalog(session: Session) -> None:
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    session.add_all(
        [
            CompanyAlias(company_id=company.id, alias="mrv", alias_type="display_name"),
            CompanyAlias(company_id=company.id, alias="mrv&co", alias_type="ri_name"),
        ]
    )

    vso = MetricCatalogItem(
        slug="vso",
        name="VSO",
        category="operacional_comercial",
        canonical_unit="percentage",
        is_active=True,
    )
    vendas = MetricCatalogItem(
        slug="vendas-liquidas",
        name="Vendas Líquidas",
        category="operacional_comercial",
        canonical_unit="brl",
        is_active=True,
    )
    session.add_all([vso, vendas])
    session.flush()
    session.add_all(
        [
            MetricCatalogAlias(metric_catalog_item_id=vso.id, alias="vso"),
            MetricCatalogAlias(metric_catalog_item_id=vendas.id, alias="vendas líquidas"),
            MetricCatalogAlias(metric_catalog_item_id=vendas.id, alias="vendas liquidas"),
        ]
    )
    session.commit()


def test_semantic_processing_canonicalizes_metrics_from_pdf() -> None:
    session = build_session()
    seed_company_and_metric_catalog(session)
    document = ResultDocument(
        company_id=1,
        document_type="previa_operacional",
        source_url="https://ri.example.com/mrv-1t26.pdf",
        effective_url="https://ri.example.com/mrv-1t26.pdf",
        content_hash="abc123",
        file_size_bytes=1024,
        current_state=DocumentState.OBSERVED.value,
    )
    session.add(document)
    session.commit()

    pdf_bytes = build_pdf_bytes(
        [
            "MRV 1T26 Prévia Operacional",
            "VSO 12,5%",
            "Vendas Líquidas R$ 500 milhões",
        ]
    )

    result = DocumentSemanticProcessingService(session).process_document(
        result_document_id=document.id,
        content=pdf_bytes,
        source_url=document.source_url,
        document_type=document.document_type or "previa_operacional",
    )

    assert result.document_state == "canonical"
    assert result.canonical_metric_count >= 2

    refreshed_document = session.get(ResultDocument, document.id)
    assert refreshed_document is not None
    assert refreshed_document.current_state == DocumentState.CANONICAL.value

    metrics = session.scalars(select(models.CanonicalMetric).order_by(models.CanonicalMetric.id.asc())).all()
    assert len(metrics) >= 2
