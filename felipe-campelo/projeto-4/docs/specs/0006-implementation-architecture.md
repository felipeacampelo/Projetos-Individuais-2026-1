# Spec 0006: Arquitetura de Implementação da V1

Esta especificação traduz as decisões de domínio em uma arquitetura implementável em Python. Ela define estrutura de diretórios, módulos, modelos persistidos, fluxos internos e ordem recomendada de entrega.

## Objetivos

- Reduzir decisões abertas antes de começar a codar.
- Manter uma arquitetura simples o bastante para a entrega.
- Separar claramente domínio, ingestão, extração, canonização e API.
- Permitir evolução sem refatoração estrutural imediata.

## Princípio de arquitetura

A v1 deve ser um **monólito modular**. Não haverá microserviços, filas distribuídas obrigatórias nem múltiplos processos independentes como premissa arquitetural.

Razões:

- o projeto acadêmico pede robustez sem exigir escala distribuída;
- a complexidade principal é semântica, não de throughput;
- o monólito modular preserva clareza e reduz custo de integração.

## Stack de implementação

- `Python 3.12`
- `FastAPI` para API HTTP
- `SQLAlchemy 2.x` para persistência
- `Alembic` para migrações
- `PostgreSQL` como banco principal
- `Pydantic v2` para contratos internos e externos
- `httpx` para coleta HTTP
- `BeautifulSoup4` para parsing HTML
- `Playwright` apenas em fontes que exigirem renderização
- `PyMuPDF` para parsing inicial de PDF
- cliente de LLM encapsulado atrás de porta própria
- `APScheduler` para monitoramento contínuo dentro do processo da aplicação ou em runner dedicado do mesmo código

## Estrutura de diretórios

```text
src/
  app/
    main.py
    config.py
    db/
      base.py
      session.py
      models/
    api/
      dependencies.py
      routers/
        health.py
        companies.py
        metrics.py
        conjuntura.py
        documents.py
        ingest.py
      schemas/
    domain/
      value_objects/
      services/
      policies/
      catalog/
    ingestion/
      scheduler.py
      jobs.py
      source_registry.py
      signal_discovery/
      fetchers/
      pdf/
    extraction/
      contracts/
      parsers/
      chunking/
      llm/
      pipelines/
    canonization/
      normalizers/
      resolvers/
      evaluators/
    repositories/
    seeds/
    observability/
tests/
  unit/
  integration/
  fixtures/
```

## Responsabilidade por módulo

### `app/main.py`

- cria a aplicação FastAPI
- registra routers
- inicializa startup e shutdown
- não contém regra de negócio

### `app/config.py`

- centraliza leitura de ambiente
- expõe settings tipados

### `app/db/models/`

- contém apenas modelos persistidos e relacionamentos
- não contém lógica de domínio complexa

### `app/api/routers/`

- expõe contratos HTTP
- chama serviços de aplicação
- não conhece detalhes de parsing ou LLM

### `app/domain/`

- contém conceitos centrais do domínio
- políticas como:
  - precedência de documento
  - precedência de evidência
  - completude semântica
  - critérios de cobertura canônica

### `app/ingestion/`

- monitora fontes
- descobre sinais
- recupera arquivos
- calcula hash
- cria ou atualiza registros de documento

### `app/extraction/`

- parsing bruto do PDF
- chunking
- preparação de prompt
- chamada ao LLM
- validação do `Contrato Semântico`

### `app/canonization/`

- normaliza empresa, métricas, unidades e recortes
- aplica regras de bloqueio
- promove fatos candidatos para dados canônicos

### `app/repositories/`

- abstrai consultas e escrita em banco
- separa persistência de serviço de domínio

### `app/seeds/`

- catálogo inicial de métricas
- empresas iniciais
- aliases iniciais de normalização

### `app/observability/`

- logging estruturado
- serialização de eventos operacionais
- helpers para correlação por `job_id`, `document_id`, `extraction_id`

## Fronteiras internas

### Camada de API

Recebe:

- requests HTTP

Entrega:

- responses HTTP

Depende de:

- serviços de aplicação
- schemas públicos

Não depende diretamente de:

- parser de PDF
- Playwright
- cliente LLM

### Camada de aplicação

Coordena casos de uso:

- rodar ingestão
- consultar conjuntura
- listar documentos
- listar empresas

Ela orquestra repositórios e serviços de domínio, mas não deve acumular regra de canonização de baixo nível.

### Camada de domínio

Contém regras estáveis e testáveis sem I/O:

- `DocumentPrecedencePolicy`
- `EvidencePrecedencePolicy`
- `SemanticCompletenessEvaluator`
- `CoverageEvaluator`
- `MeaningChangeGuard`

### Camada de infraestrutura

Implementa:

- PostgreSQL
- clientes HTTP
- Playwright
- cliente do LLM
- parser de PDF

## Modelos persistidos da v1

Os nomes abaixo devem ser usados como referência de implementação. Os nomes concretos em SQLAlchemy podem acompanhar os mesmos identificadores.

### `Company`

Campos mínimos:

- `id`
- `slug`
- `display_name`
- `is_active`
- `created_at`
- `updated_at`

### `CompanyAlias`

- `id`
- `company_id`
- `alias`
- `alias_type`

`alias_type` inicial:

- `display_name`
- `ticker`
- `ri_name`

### `PublicationSource`

- `id`
- `company_id`
- `name`
- `source_type`
- `url`
- `priority`
- `is_active`

`source_type` inicial:

- `results_page`
- `downloads_page`
- `feed`

### `MonitoringJob`

- `id`
- `scope_type`
- `scope_value`
- `status`
- `started_at`
- `finished_at`
- `error_message`

### `PublicationSignal`

- `id`
- `job_id`
- `company_id`
- `publication_source_id`
- `signal_url`
- `signal_title`
- `discovered_at`
- `processing_status`

### `ResultDocument`

- `id`
- `company_id` opcional até resolução
- `document_type`
- `source_url`
- `effective_url`
- `content_hash`
- `file_size_bytes`
- `published_at` opcional
- `current_state`
- `first_seen_at`
- `last_seen_at`

### `DocumentDiscoveryLink`

Tabela associativa para preservar `Histórico de Descoberta`.

Campos mínimos:

- `id`
- `result_document_id`
- `publication_signal_id`

### `DocumentVersionGroup`

Agrupa documentos da mesma empresa e mesmo `Período de Referência`.

Campos mínimos:

- `id`
- `company_id`
- `reference_year`
- `reference_quarter`

### `DocumentVersion`

- `id`
- `document_version_group_id`
- `result_document_id`
- `version_rank`
- `is_canonical_for_scope`
- `superseded_by_document_id` opcional

### `ExtractionRun`

- `id`
- `result_document_id`
- `contract_version`
- `llm_provider`
- `llm_model`
- `status`
- `started_at`
- `finished_at`
- `raw_contract_payload`

### `CandidateFact`

- `id`
- `extraction_run_id`
- `reported_metric_name`
- `candidate_metric_category`
- `value_status`
- `reported_value`
- `reported_unit`
- `canonical_numeric_value`
- `canonical_unit_hint`
- `warnings_json`

### `CandidateFactCut`

- `id`
- `candidate_fact_id`
- `dimension_label`
- `value_label`
- `is_material`

### `ExtractionEvidence`

- `id`
- `candidate_fact_id`
- `page_number`
- `section_label`
- `snippet`

### `MetricCatalogItem`

- `id`
- `slug`
- `name`
- `category`
- `canonical_unit`
- `is_active`

### `MetricCatalogAlias`

- `id`
- `metric_catalog_item_id`
- `alias`

### `CanonicalMetric`

- `id`
- `company_id`
- `result_document_id`
- `metric_catalog_item_id`
- `reference_year`
- `reference_quarter`
- `value`
- `value_status`
- `canonical_unit`
- `reported_value`
- `reported_unit`
- `coverage_status`

### `CanonicalMetricCut`

- `id`
- `canonical_metric_id`
- `dimension`
- `value`

### `NormalizationKnowledgeVersion`

- `id`
- `version`
- `description`
- `is_active`
- `created_at`

## Serviços principais

### `RunMonitoringJobService`

Responsável por:

- selecionar fontes
- executar descoberta
- iniciar tentativas de recuperação
- persistir sinais

### `RecoverDocumentFromSignalService`

- baixa conteúdo
- calcula hash
- deduplica
- cria ou reutiliza `ResultDocument`

### `ParseAndExtractDocumentService`

- extrai texto do PDF
- decide `full scan` ou chunking
- chama pipeline de extração
- persiste `ExtractionRun`

### `CanonizeExtractionService`

- resolve empresa e período finais
- normaliza fatos
- decide `CanonicalMetric` versus `CandidateFact` bloqueado
- atualiza estado do documento

### `ReevaluateCanonicalSourceService`

- compara nova versão com fonte atual
- promove ou rebaixa documentos

### `QueryConjunturaService`

- recebe filtros de API
- resolve aliases
- consulta apenas dados canônicos
- devolve `Cobertura Canônica` explícita

## Ordem de implementação recomendada

### Fase 1: fundação

- `config.py`
- sessão de banco
- modelos SQLAlchemy base
- Alembic inicial
- `GET /health`

### Fase 2: catálogo e seeds

- seed de `Company`
- seed de `MetricCatalogItem`
- seed de aliases iniciais
- `GET /api/companies`
- `GET /api/metricas`

### Fase 3: ingestão sem LLM

- `PublicationSource`
- `MonitoringJob`
- `PublicationSignal`
- `ResultDocument`
- cálculo de hash
- deduplicação
- `POST /api/ingest/run`
- `GET /api/documentos`

### Fase 4: extração estruturada

- parser com `PyMuPDF`
- chunking simples
- schemas Pydantic do `Contrato Semântico`
- pipeline de extração
- persistência de `ExtractionRun`, `CandidateFact`, `ExtractionEvidence`

### Fase 5: canonização

- normalização de empresa
- normalização de métricas
- normalização de recortes
- `CanonicalMetric`
- `CanonicalMetricCut`
- avaliação de completude
- reavaliação de fonte canônica

### Fase 6: superfície canônica

- `GET /api/conjuntura`
- shape final de cobertura
- filtros por métrica e recorte

### Fase 7: robustez

- reprocessamento por gatilho material
- observabilidade estruturada
- testes de regressão com dois layouts

## Estratégia de testes

### Unitários

- políticas de precedência
- avaliação de completude
- normalização de aliases
- resolução de estado de cobertura

### Integração

- ingestão com hash repetido
- mesma URL com conteúdo novo
- duas URLs para mesmo hash
- documento com extração válida e canonização inválida
- troca de fonte canônica entre versões

### Contrato

- validação dos payloads de `GET /api/conjuntura`
- validação do `Contrato Semântico`

### Fixtures

Manter pelo menos:

- um PDF de layout tabular
- um PDF de layout tipo apresentação
- payload esperado de extração para cada um

## Regras de simplificação aceitáveis na v1

- Um único processo pode hospedar API e scheduler se isso acelerar a entrega.
- `Playwright` pode ficar desligado por default e ser usado só por fonte específica.
- O catálogo e aliases podem começar seeded em banco ou arquivo estruturado carregado no startup.
- A primeira versão do `Conhecimento de Normalização` pode ser majoritariamente declarativa, sem engine complexa de regras.

## Anti-padrões proibidos

- lógica de canonização embutida nos routers
- prompts soltos como única fonte de verdade semântica
- duplicação de regras de unidade e recorte em vários módulos
- usar URL como identidade primária do documento
- expor `CandidateFact` diretamente no endpoint canônico

## Critérios de aceitação

- Um implementador consegue começar a codar sem decidir nova arquitetura.
- Cada módulo tem fronteira clara.
- Os modelos persistidos cobrem descoberta, documento, extração e canonização.
- A ordem de entrega permite validação incremental desde cedo.
