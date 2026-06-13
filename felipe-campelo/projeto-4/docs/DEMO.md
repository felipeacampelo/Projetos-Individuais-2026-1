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

### 5. Auditar documentos e linhagem

- `GET /api/documentos?empresa=mrv`
- `GET /api/documentos/{document_id}/linhagem`

Resultado esperado:
- documentos recuperados ou lista vazia explicavel
- cada documento com `source_url`, `content_hash` e sinais de descoberta associados

### 6. Consultar superficie canonica

- `GET /api/conjuntura?empresa=mrv&ano=2025&trimestre=4&metrica=vso`

Resultado esperado neste estado do projeto:
- resposta consistente
- cobertura explicita como `available` ou `unavailable`
- quando houver canonizacao, a resposta deve trazer evidência com `page` e `snippet`
- motivo explicito quando nao houver documento canonico

## Checklist de Entrega

- `README.md` descreve escopo, setup, endpoints e limitacoes
- `CONTEXT.md` descreve o glossario e o modelo de dominio
- `docs/TRACEABILITY.md` mostra aderencia ao enunciado
- `docs/DEMO.md` descreve a demonstracao
- `docs/specs` documenta contratos e arquitetura
- `docs/adr` registra decisoes arquiteturais
- `alembic/versions` contem a migracao inicial
- `src/app` contem o servico
- `tests/unit` contem testes iniciais

## Pontos de Atencao para Correcao

- o projeto esta forte em arquitetura, contratos, linhagem e auditoria
- a parte ainda incompleta para o criterio maximo e a substituicao do extrator heuristico por integracao LLM real em dois PDFs reais diferentes
- na apresentacao, deixar isso explicito evita vender uma completude que o codigo ainda nao entrega
