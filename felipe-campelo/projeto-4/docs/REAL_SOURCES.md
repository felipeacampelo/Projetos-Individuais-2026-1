# Fontes Reais Validadas

Este documento registra fontes oficiais conferidas para a demonstracao do projeto.

Data da verificacao: 13 de junho de 2026

## Paginas oficiais de resultados

### MRV

- pagina oficial: `https://ri.mrv.com.br/informacoes-financeiras/central-de-resultados/`

URLs oficiais identificadas na pagina:
- `https://api.mziq.com/mzfilemanager/v2/d/4b56353d-d5d9-435f-bf63-dcbf0a6c25d5/0fda6638-c71a-c1b8-c25e-e7f4eaffb78a?origin=2`

Observacao:
- a pagina oficial da MRV usa um carregamento dinamico via MZ e, no HTML estatico inspecionado em 13 de junho de 2026, a URL de PDF exposta com clareza era a de ESG.
- para demonstracao do pipeline, a pagina oficial da central ja e suficiente como fonte monitorada.

### Direcional

- pagina oficial: `https://ri.direcional.com.br/informacoes-financeiras/central-de-resultados/`

PDFs oficiais identificados no HTML da pagina em 13 de junho de 2026:
- previa operacional: `https://api.mziq.com/mzfilemanager/v2/d/ada9bc2c-f7d0-4359-9eaf-851b679ab788/b9e3e792-da8b-5e49-f50f-4c097cf08623?origin=2`
- apresentacao de resultados: `https://api.mziq.com/mzfilemanager/v2/d/ada9bc2c-f7d0-4359-9eaf-851b679ab788/058e4dfe-4d1c-a252-bd91-e31bb6f23ca2?origin=2`
- release de resultados: `https://api.mziq.com/mzfilemanager/v2/d/ada9bc2c-f7d0-4359-9eaf-851b679ab788/44d38c37-baad-14bd-442e-10af6efc7c91?origin=2`
- ITR: `https://api.mziq.com/mzfilemanager/v2/d/ada9bc2c-f7d0-4359-9eaf-851b679ab788/128a4b1b-7b15-7f04-4cd1-e775d0df1bbc?origin=2`

## Uso recomendado na demonstracao

Para demonstracao manual:

1. usar as paginas oficiais acima como `PublicationSource`
2. executar `POST /api/ingest/run`
3. conferir `GET /api/monitoramentos`
4. usar pelo menos um PDF oficial da Direcional para validar parsing e extração

## Limites atuais

- o codigo agora aponta para as paginas oficiais corretas
- a validacao automatizada de teste continua usando PDFs sinteticos em memoria para manter reprodutibilidade
- a validacao com PDFs reais permanece como roteiro manual documentado
