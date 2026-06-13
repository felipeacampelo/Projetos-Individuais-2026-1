# Matriz de Rastreabilidade

Este documento liga os requisitos do enunciado aos artefatos concretos da implementacao.

## 1. Coleta automatizada e continua

Requisito do README:
- observar continuamente as centrais de resultados
- disparar ingestao quando houver novo relatorio

Artefatos:
- `src/app/ingestion/scheduler.py`
- `src/app/ingestion/jobs.py`
- `src/app/ingestion/source_registry.py`
- `src/app/ingestion/signal_discovery/html_discovery.py`
- `src/app/ingestion/fetchers/results_page_fetcher.py`
- `src/app/api/routers/ingest.py`

Como foi atendido:
- o sistema possui fluxo de monitoramento unico reutilizado por scheduler e por chamada manual da API
- as fontes sao monitoradas por polling
- a descoberta inicial de sinais e baseada em links PDF encontrados em HTML

## 2. Idempotencia e evitar duplicidade

Requisito do README:
- antes de processar um PDF, verificar se ja foi computado
- usar hash do conteudo ou equivalente

Artefatos:
- `src/app/ingestion/document_recovery.py`
- `src/app/repositories/result_document_repository.py`
- `src/app/db/models/result_document.py`
- `tests/unit/test_monitoring_job_service.py`

Como foi atendido:
- o sistema calcula `sha256` do conteudo recuperado
- URLs diferentes com o mesmo arquivo convergem para um unico `ResultDocument`
- a descoberta adicional fica preservada em `DocumentDiscoveryLink`

## 3. Parsing e estrategia de segmentacao

Requisito do README:
- justificar `full-scan` ou `chunking`
- suportar documentos curtos e longos

Artefatos:
- `src/app/extraction/parsers/pdf_parser.py`
- `src/app/extraction/chunking/strategy.py`
- `tests/unit/test_chunking_strategy.py`
- `docs/specs/0006-implementation-architecture.md`

Como foi atendido:
- o parser base gera texto por pagina
- a estrategia de leitura e deterministica
- documentos curtos seguem `full scan`
- documentos extensos seguem `semantic chunking`

## 4. Contrato semantico como filtro de qualidade

Requisito do README:
- usar saida estruturada e versionada
- blindar o banco contra alucinacao e tipos inconsistentes

Artefatos:
- `src/app/extraction/contracts/semantic_contract.py`
- `src/app/db/models/extraction.py`
- `docs/specs/0003-semantic-contract-schema.md`

Como foi atendido:
- o contrato semantico foi modelado em Pydantic
- a persistencia prevista guarda `contract_version` e `raw_contract_payload`
- o contrato exige metadados do documento, fatos, recortes, evidencias e avisos

## 5. Catalogo de dados e linhagem

Requisito do README:
- associar cada linha ou documento ao link do PDF original

Artefatos:
- `src/app/db/models/monitoring.py`
- `src/app/db/models/result_document.py`
- `src/app/api/routers/documents.py`
- `src/app/api/routers/monitoring.py`
- `src/app/api/routers/publication_sources.py`

Como foi atendido:
- `PublicationSignal` preserva a origem observada
- `ResultDocument` preserva `source_url`, `effective_url`, `content_hash`
- `DocumentDiscoveryLink` conecta sinal e documento
- a API expõe jobs, sinais, documentos e linhagem

## 6. API por empresa e periodo

Requisito do README:
- expor uma API REST/JSON clara para consulta

Artefatos:
- `src/app/api/routers/conjuntura.py`
- `src/app/api/routers/documents.py`
- `src/app/api/routers/companies.py`
- `src/app/api/routers/metrics.py`
- `docs/specs/0002-api-contracts.md`

Como foi atendido:
- `GET /api/conjuntura` recebe `empresa`, `ano`, `trimestre`
- `GET /api/documentos` suporta filtros de auditoria
- `GET /api/companies` e `GET /api/metricas` expõem o dominio seedado

## 7. Modelagem temporal e documento canonico

Requisito do README:
- consistencia no salvamento dos trimestres
- uma fonte canonica por empresa e periodo

Artefatos:
- `docs/adr/0001-versioned-result-documents.md`
- `docs/adr/0002-centralized-semantic-source-of-truth.md`
- `src/app/canonization/service.py`
- `src/app/db/models/canonical_metric.py`
- `src/app/db/models/result_document.py`
- `src/app/repositories/document_version_repository.py`

Como foi atendido:
- a documentacao define uma unica superficie canonica por empresa e periodo
- a camada de canonizacao persiste metricas canonicas separadas do bruto
- a cobertura da consulta e explicita quando nao existe documento canonico
- o sistema persiste `DocumentVersionGroup` e `DocumentVersion` por empresa+ano+trimestre
- `GET /api/documentos` e `GET /api/documentos/{document_id}/linhagem` expõem periodo e numero de versao quando conhecidos
- uma reavaliacao inicial por precedencia de tipo documental pode mover o documento anterior para `superseded`

## 8. Criterios de avaliacao

### Qualidade do contrato semantico

Cobertura atual:
- modelagem em Pydantic pronta
- persistencia do contrato implementada
- extracao heuristica ponta a ponta preenchendo `ExtractionRun`, fatos candidatos e evidencias

Risco atual:
- falta integracao com provedor LLM real externo

### Resiliencia contra variacoes de layout

Cobertura atual:
- descoberta HTML desacoplada do layout exato
- parser e chunking sem coordenadas fixas
- extracao heuristica baseada em texto e evidencias por pagina
- testes cobrindo dois formatos sintéticos distintos:
  - linha unica no estilo tabela/resumo
  - metrica e valor quebrados em linhas separadas no estilo slide
- teste de integracao `tests/integration/test_pipeline_two_layouts_audit.py` cobre os dois layouts passando pelo pipeline completo

Risco atual:
- faltam dois fluxos PDF reais ponta a ponta demonstrados com arquivos de mercado reais

### Extracao de valores absolutos

Cobertura atual:
- contrato semantico diferencia valor reportado, unidade reportada e hint canonico
- normalizacao de unidade existe
- extrator heuristico prioriza valor absoluto aderente a unidade esperada (`R$`, `%`, `unidades`)

Risco atual:
- falta cobertura maior de layouts reais e casos ambíguos

### Modelagem temporal e API

Cobertura atual:
- API publica foi documentada
- cobertura explicita em `GET /api/conjuntura`
- observabilidade basica com logs estruturados correlacionados e motivos explicitos de falha em `GET /api/monitoramentos`
- reavaliacao canônica agora remove métricas do documento supersedido para manter uma única fonte canônica ativa por empresa e período
- o documento persiste `contract_version_used` e `normalization_version_used`, e isso já alimenta elegibilidade de reprocessamento material

Risco atual:
- a reavaliacao ainda nao compara completude semantica de forma sofisticada entre duas versoes do mesmo periodo
