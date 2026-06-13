# Spec 0002: Contratos da API

Esta especificação define a `Superfície Canônica` e os endpoints auxiliares da v1. Ela complementa a [Spec 0001](./0001-pipeline-uda-ri-habitacional.md) e usa os termos definidos em [CONTEXT.md](../../CONTEXT.md).

## Objetivos

- Expor dados canônicos com semântica estável.
- Tornar ausência de cobertura explícita.
- Separar API pública canônica de endpoints operacionais.
- Permitir auditoria mínima sem expor toda a complexidade interna do pipeline.

## Convenções gerais

- Todos os payloads são `application/json`.
- Todos os timestamps são `ISO 8601` em UTC.
- Todos os campos monetários canônicos são expressos em reais absolutos.
- Todos os slugs são minúsculos, estáveis e URL-safe.
- A API principal nunca expõe `Métrica Candidata`, `Sinal de Publicação` ou estados operacionais brutos.

## Endpoint principal

## `GET /api/conjuntura`

Retorna a coleção de `Métricas` canônicas para um escopo temporal explícito.

### Query parameters

- `empresa`: obrigatório; `Slug de Empresa` ou alias normalizável.
- `ano`: obrigatório; inteiro de quatro dígitos.
- `trimestre`: obrigatório; inteiro `1..4`.
- `metrica`: opcional; slug ou nome canônico normalizável da métrica.
- `dimensao_recorte`: opcional; filtra por tipo de recorte.
- `valor_recorte`: opcional; filtra por valor normalizado do recorte.

### Regras

- Se `empresa` não puder ser normalizada para uma `Empresa`, responder `404`.
- Se `ano` ou `trimestre` forem inválidos, responder `422`.
- Se o escopo existir, mas não houver `Cobertura Canônica`, responder `200` com `coverage.status = "unavailable"`.
- Se houver cobertura, responder `200` com `coverage.status = "available"` e a coleção de métricas.
- Lista vazia por si só nunca representa ausência de cobertura.

### Response shape

```json
{
  "query": {
    "empresa": "mrv",
    "ano": 2025,
    "trimestre": 3,
    "metrica": null,
    "dimensao_recorte": null,
    "valor_recorte": null
  },
  "coverage": {
    "status": "available",
    "company_slug": "mrv",
    "reference_period": {
      "year": 2025,
      "quarter": 3
    },
    "canonical_document": {
      "document_id": "doc_01",
      "document_type": "previa_operacional",
      "source_url": "https://ri.exemplo.com/3t25.pdf",
      "published_at": "2025-10-10T12:00:00Z"
    }
  },
  "data": [
    {
      "metric_slug": "vendas-liquidas",
      "metric_name": "Vendas Líquidas",
      "value": 420000000.0,
      "value_status": "reported",
      "canonical_unit": "brl",
      "reported_unit": "R$ milhões",
      "reported_value": 420.0,
      "cuts": [
        {
          "dimension": "escopo",
          "value": "consolidado"
        }
      ],
      "evidence": {
        "page": 7,
        "section": "Destaques Operacionais",
        "snippet": "Vendas líquidas totalizaram R$ 420 milhões no 3T25."
      }
    }
  ],
  "meta": {
    "returned_metrics": 1,
    "generated_at": "2026-06-12T12:00:00Z"
  }
}
```

### `coverage.status`

Valores permitidos:

- `available`
- `unavailable`

Quando `unavailable`, `data` deve ser lista vazia e `coverage.reason` deve existir com um valor padronizado:

- `no_canonical_document`
- `canonicalization_failed`
- `document_not_found_for_scope`

### `value_status`

Valores permitidos:

- `reported`: há `Valor Absoluto`.
- `missing`: a métrica existe canonicamente, mas o valor principal é `null`.

`value_status = "missing"` exige:

- `value = null`
- `reported_value = null`
- `canonical_unit` presente se a unidade da métrica for conhecida

## Endpoint de empresas

## `GET /api/companies`

Retorna empresas disponíveis para consulta.

### Response shape

```json
{
  "data": [
    {
      "slug": "mrv",
      "display_name": "MRV",
      "aliases": ["mrv&co", "mrv engenharia"],
      "tickers": ["MRVE3"]
    }
  ]
}
```

## Endpoint de métricas canônicas

## `GET /api/metricas`

Retorna o `Catálogo de Métricas` visível para a API principal.

### Query parameters

- `q`: opcional; busca por nome ou alias.

### Response shape

```json
{
  "data": [
    {
      "slug": "vendas-liquidas",
      "name": "Vendas Líquidas",
      "category": "operacional",
      "canonical_unit": "brl"
    }
  ]
}
```

## Endpoint de documentos

## `GET /api/documentos`

Endpoint auxiliar para auditoria e operação. Não faz parte da `Superfície Canônica`.

### Query parameters

- `empresa`: opcional
- `ano`: opcional
- `trimestre`: opcional
- `status`: opcional
- `canonical_only`: opcional booleano

### Response mínima

```json
{
  "data": [
    {
      "document_id": "doc_01",
      "company_slug": "mrv",
      "reference_period": {
        "year": 2025,
        "quarter": 3
      },
      "document_type": "previa_operacional",
      "status": "canonical",
      "source_url": "https://ri.exemplo.com/3t25.pdf",
      "content_hash": "sha256:abc123",
      "published_at": "2025-10-10T12:00:00Z",
      "is_canonical": true
    }
  ]
}
```

### Statuses de documento

Valores permitidos na v1:

- `observed`
- `failed_recovery`
- `failed_interpretation`
- `failed_canonicalization`
- `canonical`
- `superseded`

## Endpoint de disparo manual

## `POST /api/ingest/run`

Dispara execução controlada do pipeline para operação e testes.

### Request body

```json
{
  "company_slug": "mrv",
  "force_reprocess": false
}
```

### Regras

- `company_slug` é opcional; ausente significa execução para todas as empresas ativas.
- `force_reprocess = true` não ignora regras de domínio; apenas habilita reavaliação de itens elegíveis.
- O endpoint responde aceitação de job, não resultado final síncrono.

### Response shape

```json
{
  "job_id": "job_01",
  "status": "accepted",
  "requested_scope": {
    "company_slug": "mrv",
    "force_reprocess": false
  }
}
```

## Healthcheck

## `GET /health`

### Response shape

```json
{
  "status": "ok",
  "service": "pipeline-uda-ri-habitacional",
  "generated_at": "2026-06-12T12:00:00Z"
}
```

## Erros

### Error shape

```json
{
  "error": {
    "code": "invalid_query_parameter",
    "message": "trimestre must be between 1 and 4"
  }
}
```

### Error codes da v1

- `invalid_query_parameter`
- `unknown_company`
- `unknown_metric`
- `invalid_request_body`
- `job_dispatch_failed`
- `internal_error`

## Defaults de implementação

- FastAPI com validação por Pydantic.
- Normalização de aliases de empresa e métrica acontece antes da consulta principal.
- Paginação não é obrigatória na v1 para `GET /api/conjuntura`, mas deve ser fácil de adicionar depois.
- `GET /api/documentos` pode receber paginação na implementação já na v1 se isso simplificar.

## Critérios de aceitação

- `GET /api/conjuntura` diferencia claramente cobertura indisponível de lista vazia por filtro legítimo.
- O endpoint principal retorna somente métricas canônicas.
- A resposta do endpoint principal inclui metadados mínimos de auditabilidade.
- `GET /api/companies` e `GET /api/metricas` refletem apenas entidades já normalizadas para uso público.
- `POST /api/ingest/run` não bloqueia aguardando processamento completo.
