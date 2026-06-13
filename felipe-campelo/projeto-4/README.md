# Projeto Individual 4 - Pipeline de UDA para RI Habitacional

Implementacao inicial de um pipeline de engenharia e analise de dados nao estruturados para documentos trimestrais de Relacoes com Investidores de incorporadoras do setor habitacional.

## Objetivo

O servico monitora fontes de publicacao, detecta novos PDFs, deduplica por hash, registra linhagem auditavel do documento e expoe uma API REST para consulta da cobertura canonica por empresa e periodo.

## Escopo Implementado

- monitoramento de fontes de RI por empresa
- descoberta automatica de links PDF em paginas HTML de resultados
- recuperacao de documentos com deduplicacao por `sha256`
- trilha de descoberta entre `job -> signal -> document`
- parser base de PDF e heuristica de `full scan` vs `semantic chunking`
- contrato semantico versionado em Pydantic
- extracao semantica heuristica ponta a ponta para metricas iniciais do catalogo
- normalizacao inicial de empresa, metrica, unidade e recortes
- persistencia de metricas canonicas
- versionamento de documentos por empresa e periodo
- API REST para health, empresas, metricas, ingestao, documentos, fontes de publicacao, monitoramentos e conjuntura

## Estrutura

- `src/app`: codigo da aplicacao
- `alembic`: migracoes
- `docs/specs`: especificacoes orientadas a contrato
- `docs/adr`: decisoes arquiteturais
- `docs/TRACEABILITY.md`: mapa entre requisitos do enunciado e artefatos implementados
- `docs/DEMO.md`: roteiro de demonstracao e checklist de entrega
- `docs/REAL_SOURCES.md`: registro das fontes oficiais reais verificadas para a demo
- `tests`: testes unitarios e fixtures
- `CONTEXT.md`: glossario e modelo de dominio

## Ordem Recomendada de Leitura

Para correcao, a leitura recomendada e:

1. `README.md`
2. `CONTEXT.md`
3. `docs/TRACEABILITY.md`
4. `docs/DEMO.md`
5. `docs/REAL_SOURCES.md`
6. `docs/specs/0001-pipeline-uda-ri-habitacional.md`
7. `docs/specs/0002-api-contracts.md`
8. `docs/specs/0003-semantic-contract-schema.md`
9. `docs/specs/0004-ingestion-and-document-lifecycle.md`
10. `docs/specs/0005-initial-housing-metric-catalog.md`
11. `docs/specs/0006-implementation-architecture.md`
12. `docs/specs/0007-implementation-backlog.md`
13. `docs/adr/0001-versioned-result-documents.md`
14. `docs/adr/0002-centralized-semantic-source-of-truth.md`

## Setup

Requer Python 3.12 e PostgreSQL local.

```zsh
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://SEU_USUARIO:postgres@localhost:5432/pipeline_uda"
alembic upgrade head
PYTHONPATH=src python -m app.seeds.load
uvicorn --app-dir src app.main:app --reload
```

## Endpoints Principais

- `GET /health`
- `GET /api/companies`
- `GET /api/metricas`
- `GET /api/fontes-publicacao`
- `GET /api/monitoramentos`
- `GET /api/monitoramentos/{job_id}`
- `POST /api/ingest/run`
- `GET /api/documentos`
- `GET /api/documentos/{document_id}/linhagem`
- `GET /api/conjuntura?empresa=mrv&ano=2025&trimestre=4&metrica=vso`

## Validacao Rapida

1. Suba a API e abra `/docs`.
2. Execute `POST /api/ingest/run` para `mrv` ou `direcional`.
3. Consulte `GET /api/monitoramentos` e `GET /api/monitoramentos/{job_id}` para auditar sinais detectados, incluindo `failure_stage` e `failure_reason` quando houver erro.
4. Consulte `GET /api/documentos` e `GET /api/documentos/{document_id}/linhagem` para ver a linhagem do PDF.
5. Consulte `GET /api/conjuntura` para verificar cobertura canonica por periodo.

## Validacao Manual com PDF Real

Para validar um PDF oficial diretamente, sem depender da API:

```zsh
PYTHONPATH=src python -m app.tools.validate_real_pdf --url "URL_OFICIAL_DO_PDF" --document-type previa_operacional
```

Exemplo com URL oficial documentada:

```zsh
PYTHONPATH=src python -m app.tools.validate_real_pdf --url "https://api.mziq.com/mzfilemanager/v2/d/ada9bc2c-f7d0-4359-9eaf-851b679ab788/b9e3e792-da8b-5e49-f50f-4c097cf08623?origin=2" --document-type previa_operacional
```

## Aderencia ao Enunciado

### Extracao automatizada e continua

- o projeto possui scheduler com `APScheduler`
- a ingestao manual e periodica reaproveita o mesmo fluxo de monitoramento
- a deteccao inicial usa polling em paginas de resultados

### Idempotencia e evitar duplicidade

- cada documento recuperado gera `sha256`
- conteudos identicos publicados em URLs diferentes convergem para um unico `ResultDocument`

### Contrato semantico

- os contratos de saida estruturada estao em `src/app/extraction/contracts/semantic_contract.py`
- a extração prevista e versionada persiste `contract_version` e `raw_contract_payload`

### Catalogo de dados e linhagem

- cada documento preserva `source_url`, `effective_url` e `content_hash`
- cada descoberta gera `PublicationSignal`
- a relacao entre sinal e documento fica em `DocumentDiscoveryLink`
- a API expõe essa trilha em `GET /api/documentos/{document_id}/linhagem`

### Observabilidade e falhas explicaveis

- `StructuredLogger` emite logs JSON com correlacao minima por `job_id`, `signal_id`, `document_id` e `extraction_id`
- `GET /api/monitoramentos` e `GET /api/monitoramentos/{job_id}` expõem `failure_stage` e `failure_reason`
- falhas de `source_fetch`, `recovery`, `interpretation` e `canonicalization` ficam registradas para auditoria

### API por empresa e periodo

- `GET /api/conjuntura` exige `empresa`, `ano` e `trimestre`
- `GET /api/documentos` permite filtro por empresa e status

## Estado Atual e Limitacoes

- a camada de extracao semantica com LLM esta estruturada, mas ainda nao foi ligada a um provedor real
- a extracao semantica atual usa um cliente heuristico local para demonstracao, nao um provedor externo real
- a demonstracao completa com dois layouts PDF reais ainda depende da inclusao de fixtures PDF reais adicionais e ampliacao das heuristicas
- a reavaliacao automatica por precedencia documental foi implementada de forma inicial, mas ainda sem politica completa de completude semantica comparativa

## Entregaveis

- codigo-fonte da aplicacao
- migracoes Alembic
- seeds minimos do dominio
- contratos da API
- contrato semantico versionado
- ADRs e especificacoes de arquitetura
- testes unitarios iniciais
- documentacao de rastreabilidade e demonstracao

## Testes

```zsh
PYTHONPATH=src pytest tests/unit/test_chunking_strategy.py tests/unit/test_document_lifecycle.py tests/unit/test_monitoring_job_service.py tests/unit/test_semantic_processing.py tests/unit/test_document_version_repository.py tests/unit/test_canonical_source_service.py
```
