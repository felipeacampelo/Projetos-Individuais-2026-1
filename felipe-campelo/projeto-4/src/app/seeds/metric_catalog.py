from __future__ import annotations

METRIC_CATALOG_SEED_DATA = [
    {
        "slug": "vendas-liquidas",
        "name": "Vendas Líquidas",
        "category": "operacional_comercial",
        "canonical_unit": "brl",
        "aliases": ["vendas liquidas", "venda líquida", "net sales"],
    },
    {
        "slug": "vso",
        "name": "VSO",
        "category": "operacional_comercial",
        "canonical_unit": "percentage",
        "aliases": ["vso", "velocidade de vendas", "sales over supply"],
    },
    {
        "slug": "lancamentos-valor",
        "name": "Lançamentos",
        "category": "lancamentos",
        "canonical_unit": "brl",
        "aliases": ["lançamentos", "lancamentos", "gross launches", "psv lançado", "valor de lançamentos"],
    },
    {
        "slug": "lancamentos-unidades",
        "name": "Unidades Lançadas",
        "category": "lancamentos",
        "canonical_unit": "units",
        "aliases": ["unidades lançadas", "qtd lançada", "launch units"],
    },
    {
        "slug": "estoque-valor",
        "name": "Estoque",
        "category": "estoque",
        "canonical_unit": "brl",
        "aliases": ["estoque", "inventory"],
    },
    {
        "slug": "estoque-unidades",
        "name": "Unidades em Estoque",
        "category": "estoque",
        "canonical_unit": "units",
        "aliases": ["unidades em estoque", "estoque em unidades", "inventory units"],
    },
    {
        "slug": "unidades-vendidas",
        "name": "Unidades Vendidas",
        "category": "unidades",
        "canonical_unit": "units",
        "aliases": ["unidades vendidas", "sales units", "qtd vendida"],
    },
    {
        "slug": "unidades-repassadas",
        "name": "Unidades Repassadas",
        "category": "unidades",
        "canonical_unit": "units",
        "aliases": ["repasses", "unidades repassadas", "units transferred"],
    },
    {
        "slug": "banco-de-terrenos-valor",
        "name": "Banco de Terrenos",
        "category": "terrenos",
        "canonical_unit": "brl",
        "aliases": ["banco de terrenos", "landbank", "land bank"],
    },
    {
        "slug": "banco-de-terrenos-potencial",
        "name": "Potencial do Banco de Terrenos",
        "category": "terrenos",
        "canonical_unit": "units",
        "aliases": ["potencial do banco de terrenos", "landbank potential", "potencial em unidades"],
    },
]
