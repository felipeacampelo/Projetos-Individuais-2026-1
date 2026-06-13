from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Company, CompanyAlias, MetricCatalogAlias, MetricCatalogItem, PublicationSource
from app.seeds.companies import COMPANY_SEED_DATA
from app.seeds.metric_catalog import METRIC_CATALOG_SEED_DATA
from app.seeds.publication_sources import PUBLICATION_SOURCE_SEED_DATA


def seed_companies(session: Session) -> None:
    for company_data in COMPANY_SEED_DATA:
        company = session.scalar(select(Company).where(Company.slug == company_data["slug"]))
        if company is None:
            company = Company(
                slug=company_data["slug"],
                display_name=company_data["display_name"],
                is_active=True,
            )
            session.add(company)
            session.flush()

        existing_aliases = {alias.alias for alias in company.aliases}
        for alias_data in company_data["aliases"]:
            if alias_data["alias"] in existing_aliases:
                continue
            session.add(
                CompanyAlias(
                    company_id=company.id,
                    alias=alias_data["alias"],
                    alias_type=alias_data["alias_type"],
                )
            )


def seed_metric_catalog(session: Session) -> None:
    for item_data in METRIC_CATALOG_SEED_DATA:
        item = session.scalar(select(MetricCatalogItem).where(MetricCatalogItem.slug == item_data["slug"]))
        if item is None:
            item = MetricCatalogItem(
                slug=item_data["slug"],
                name=item_data["name"],
                category=item_data["category"],
                canonical_unit=item_data["canonical_unit"],
                is_active=True,
            )
            session.add(item)
            session.flush()

        existing_aliases = {alias.alias for alias in item.aliases}
        for alias in item_data["aliases"]:
            if alias in existing_aliases:
                continue
            session.add(
                MetricCatalogAlias(
                    metric_catalog_item_id=item.id,
                    alias=alias,
                )
            )


def seed_publication_sources(session: Session) -> None:
    companies_by_slug = {
        company.slug: company for company in session.scalars(select(Company)).all()
    }
    for source_data in PUBLICATION_SOURCE_SEED_DATA:
        company = companies_by_slug.get(source_data["company_slug"])
        if company is None:
            continue

        existing = session.scalar(
            select(PublicationSource).where(
                PublicationSource.company_id == company.id,
                PublicationSource.url == source_data["url"],
            )
        )
        if existing is not None:
            continue

        session.add(
            PublicationSource(
                company_id=company.id,
                name=source_data["name"],
                source_type=source_data["source_type"],
                url=source_data["url"],
                priority=source_data["priority"],
                is_active=True,
            )
        )


def run_all_seeds(session: Session) -> None:
    seed_companies(session)
    seed_metric_catalog(session)
    seed_publication_sources(session)
    session.commit()
