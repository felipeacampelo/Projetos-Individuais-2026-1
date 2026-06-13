# Roteiro de Demonstracao e Checklist de Entrega

## Objetivo da Demonstracao

Mostrar que o sistema:
- monitora fontes de RI
- detecta sinais de novos PDFs
- deduplica documentos por hash
- executa extracao semantica minima
- canoniza metricas para consulta estruturada
- preserva linhagem auditavel
- expõe API consultavel por empresa e periodo

## Preparacao do Ambiente

```zsh
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://SEU_USUARIO:postgres@localhost:5432/pipeline_uda"
alembic upgrade head
PYTHONPATH=src python -m app.seeds.load
uvicorn --app-dir src app.main:app --reload
```

## Fontes Oficiais Recomendadas

Consultar tambem:

- `docs/REAL_SOURCES.md`

Paginas oficiais verificadas em 13 de junho de 2026:

- MRV: `https://ri.mrv.com.br/informacoes-financeiras/central-de-resultados/`
- Direcional: `https://ri.direcional.com.br/informacoes-financeiras/central-de-resultados/`

## Passo a Passo da Demo

### 1. Verificar saude do servico

- abrir `GET /health`
- resultado esperado: `status = ok`

### 2. Verificar dominio seedado

- `GET /api/companies`
- `GET /api/metricas`
- `GET /api/fontes-publicacao`

Resultado esperado:
- empresas `mrv` e `direcional`
- catalogo inicial de metricas
- uma fonte ativa por empresa seedada
- as URLs seedadas devem apontar para as centrais oficiais corretas

### 3. Disparar monitoramento

- executar `POST /api/ingest/run`
- body sugerido:

```json
{
  "company_slug": "mrv",
  "force_reprocess": false
}
```

Resultado esperado:
- retorno com `job_id`
- status de execucao do job

### 4. Auditar trilha do job

- `GET /api/monitoramentos`
- `GET /api/monitoramentos/{job_id}`

Resultado esperado:
- visualizar job criado
- visualizar sinais detectados
- visualizar `processing_status` de cada sinal
- quando houver erro, visualizar `failure_stage` e `failure_reason`

### 5. Auditar documentos e linhagem

- `GET /api/documentos?empresa=mrv`
- `GET /api/documentos/{document_id}/linhagem`

Resultado esperado:
- documentos recuperados ou lista vazia explicavel
- cada documento com `source_url`, `content_hash`, periodo e numero de versao quando conhecidos
- cada documento com sinais de descoberta associados
- quando houver duas versoes do mesmo periodo, a mais antiga pode aparecer como `superseded`
- se algum sinal falhar em recuperacao, interpretacao ou canonizacao, isso aparece no proprio signal

### 6. Consultar superficie canonica

- `GET /api/conjuntura?empresa=mrv&ano=2025&trimestre=4&metrica=vso`

Resultado esperado neste estado do projeto:
- resposta consistente
- cobertura explicita como `available` ou `unavailable`
- quando houver canonizacao, a resposta deve trazer evidência com `page` e `snippet`
- motivo explicito quando nao houver documento canonico

### 7. Validar um PDF oficial diretamente

Rodar:

```zsh
PYTHONPATH=src python -m app.tools.validate_real_pdf --url "https://api.mziq.com/mzfilemanager/v2/d/ada9bc2c-f7d0-4359-9eaf-851b679ab788/b9e3e792-da8b-5e49-f50f-4c097cf08623?origin=2" --document-type previa_operacional
```

Resultado esperado:
- contrato semântico em JSON
- `document.reference_period` inferido do PDF quando presente no texto
- fatos iniciais extraídos com evidência por página

## Checklist de Entrega

- `README.md` descreve escopo, setup, endpoints e limitacoes
- `CONTEXT.md` descreve o glossario e o modelo de dominio
- `docs/TRACEABILITY.md` mostra aderencia ao enunciado
- `docs/DEMO.md` descreve a demonstracao
- `docs/specs` documenta contratos e arquitetura
- `docs/adr` registra decisoes arquiteturais
- `alembic/versions` contem a migracao inicial
- `alembic/versions` contem a migracao inicial e a migracao de versionamento de documentos
- `alembic/versions` contem a migracao de auditoria de falhas de monitoramento
- `alembic/versions` contem a migracao de metadados de versao usados no reprocessamento material
- `src/app` contem o servico
- `tests/unit` contem testes iniciais
- `tests/integration/test_pipeline_two_layouts_audit.py` prova dois layouts no pipeline com auditoria completa

## Pontos de Atencao para Correcao

- o projeto esta forte em arquitetura, contratos, linhagem e auditoria
- existe uma prova automatizada de dois layouts distintos entrando no pipeline com versionamento, evidência e escolha de fonte canônica
- o pipeline já evita reprocessamento cego de duplicatas sem mudança material de contrato ou normalização
- a parte ainda incompleta para o criterio maximo e a substituicao do extrator heuristico por integracao LLM real em dois PDFs reais diferentes
- a reavaliacao canônica existe, mas ainda e simples quando duas versoes do mesmo periodo competem
- na apresentacao, deixar isso explicito evita vender uma completude que o codigo ainda nao entrega
