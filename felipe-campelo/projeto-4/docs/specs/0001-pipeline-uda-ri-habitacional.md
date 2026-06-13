# Spec 0001: Pipeline UDA para RI Habitacional

Esta especificação define a primeira versão implementável do projeto de pipeline contínuo para monitoramento de portais de RI de incorporadoras, extração semântica de métricas operacionais trimestrais e exposição dos dados por API. Os termos de domínio usados aqui seguem o glossário em [CONTEXT.md](../../CONTEXT.md).

## Objetivo

Construir um sistema contínuo que:

1. monitora `Fontes de Publicação` de `Empresas` do setor habitacional;
2. identifica novos `Documentos de Resultado`;
3. seleciona uma `Fonte Canônica` por `Empresa` e `Período de Referência`;
4. produz `Métricas` canônicas com `Evidência de Extração`;
5. expõe essas métricas por uma `Superfície Canônica` via API.

## Escopo da v1

- Cobrir `Prévia Operacional` como fonte preferencial.
- Aceitar outros `Documentos de Resultado` trimestrais quando a prévia não existir.
- Priorizar métricas operacionais e de mercado do setor habitacional relevantes para o `Boletim de Conjuntura`.
- Suportar pelo menos dois layouts de documento semanticamente diferentes.
- Expor apenas dados canônicos na API principal.

## Fora de escopo da v1

- Interface gráfica.
- Extração de todas as métricas financeiras corporativas possíveis.
- Revisão humana obrigatória no fluxo principal.
- Generalização para setores fora do habitacional.

## Invariantes de domínio

- O `Período de Referência` é sempre o trimestre declarado no documento, nunca inferido da data de publicação.
- A `Identidade do Documento` é definida pelo conteúdo do arquivo, não pela URL.
- Uma `Empresa` possui `Slug de Empresa` estável e pode ter múltiplas `Fontes de Publicação`.
- A `Fonte Canônica` é única por `Empresa` + `Período de Referência`.
- `Prévia Operacional` tem precedência sobre outros `Documentos de Resultado` elegíveis.
- `Valor Absoluto` sempre tem prioridade sobre percentuais e variações.
- `Valor Ausente` é representado como `null`, nunca inferido.
- `Métrica` canônica só entra na `Superfície Canônica` após `Extração`, `Contrato Semântico`, `Normalização Semântica` e `Canonização`.
- `Cobertura Canônica` ausente, `Valor Ausente` e `Métrica Inexistente` são estados distintos.

## Modelo conceitual

### Empresa

- Identidade canônica consultável da API.
- Possui `Slug de Empresa` estável.
- Pode ter aliases nominais e tickers.
- Pode ter múltiplas `Fontes de Publicação` com `Prioridade de Fonte`.

### Fonte de Publicação

- Canal monitorável de RI pertencente a uma `Empresa`.
- Pode gerar `Sinais de Publicação`.
- Pode ser página de resultados, listagem de downloads, release center ou feed.

### Sinal de Publicação

- Evidência preliminar de possível novo documento.
- Ainda não é um `Documento Observado`.
- Múltiplos sinais podem convergir para o mesmo documento e formar `Histórico de Descoberta`.

### Documento de Resultado

- Documento trimestral relevante para o domínio.
- Pode ter múltiplas `Versões de Documento` para o mesmo período.
- Uma nova versão só substitui a `Fonte Canônica` após `Reavaliação de Fonte Canônica`.

### Métrica

- Fato estruturado de uma `Fonte Canônica`.
- Inclui nome canônico, valor, `Unidade Canônica`, escala normalizada e um conjunto sem ordem de `Recortes de Métrica`.
- Métricas monetárias são normalizadas para `Escala Monetária Canônica` em reais absolutos.
- `%` e `p.p.` são unidades semanticamente distintas.

### Evidência de Extração

- Liga a métrica ao documento, página ou seção e trecho textual de suporte.
- É obrigatória para métrica canônica.

## Regras de canonização

- A `Superfície Canônica` expõe somente métricas vindas de `Fonte Canônica`.
- Quando houver conflito interno no documento, aplica-se `Precedência de Evidência`:
  1. tabela explícita do período corrente;
  2. quadro-resumo operacional do período corrente;
  3. texto corrido;
  4. material comparativo ou promocional.
- `Mudança de Layout` não impede canonização.
- Indícios de `Mudança de Significado` bloqueiam canonização e mantêm o dado como `Métrica Candidata`.
- `Recorte de Métrica` materialmente ambíguo bloqueia canonização.
- Métrica ou recorte ainda não normalizados permanecem internos até resolução pelo `Conhecimento de Normalização`.

## Contrato semântico

- O `Contrato Semântico` é versionável.
- Cada extração deve registrar a versão do contrato usada.
- O contrato exige:
  - empresa identificável;
  - período identificável;
  - tipo de documento;
  - coleção de fatos candidatos;
  - ausência explícita com `null`;
  - evidências mínimas por fato.
- Schema válido não implica canonização automática.

## Reprocessamento

- `Falha de Recuperação`, `Falha de Interpretação` e `Falha de Canonização` são estados recuperáveis.
- `Reprocessamento` só ocorre por `Gatilho de Reprocessamento` material:
  - nova `Versão de Documento`;
  - novo conteúdo recuperável;
  - evolução de `Normalização Semântica`;
  - evolução do `Contrato Semântico`;
  - melhoria relevante de interpretação.
- Reexecução cega em lote não é comportamento desejado.

## Superfície Canônica

### Endpoint principal

`GET /api/conjuntura`

Filtros mínimos:

- `empresa`
- `ano`
- `trimestre`
- `metrica` opcional

Regras:

- `Escopo Temporal Explícito` é obrigatório.
- A resposta principal é uma coleção de `Métricas` normalizadas.
- A resposta inclui metadados mínimos de auditabilidade:
  - slug da empresa;
  - período;
  - nome canônico da métrica;
  - valor normalizado;
  - unidade canônica;
  - unidade ou escala original quando relevante;
  - recortes canônicos;
  - referência resumida da evidência;
  - estado de `Cobertura Canônica`.

### Endpoints auxiliares

- `GET /api/companies`
- `GET /api/documentos`
- `GET /api/metricas`
- `POST /api/ingest/run`
- `GET /health`

Os endpoints auxiliares podem expor `Documentos Observados`, `Métricas Candidatas` e estados operacionais, mas isso fica fora da `Superfície Canônica`.

## Defaults técnicos adotados

- Linguagem: Python 3.12
- API: FastAPI
- Banco relacional: PostgreSQL
- Scheduler: APScheduler ou cron equivalente
- Descoberta/coleta: httpx + BeautifulSoup, com Playwright apenas quando a página exigir renderização
- Parsing inicial de PDF: PyMuPDF
- Saída estruturada do LLM: Pydantic
- Estratégia de processamento:
  - `full scan` para documentos curtos;
  - chunking semântico para documentos longos;
  - seleção de páginas e trechos candidatos antes da chamada ao LLM.

## Estrutura mínima de dados

- `companies`
- `publication_sources`
- `publication_signals`
- `result_documents`
- `document_versions`
- `document_observations`
- `extractions`
- `extraction_evidence`
- `canonical_metrics`
- `candidate_metrics`
- `metric_catalog`
- `normalization_knowledge`

Os nomes concretos podem variar na implementação, mas a separação conceitual acima é obrigatória.

## Critérios de aceitação da v1

- O sistema monitora continuamente pelo menos duas `Empresas`.
- O sistema evita reprocessar o mesmo documento por identidade de conteúdo.
- O sistema mantém histórico de versões de documento no mesmo período.
- O sistema canoniza pelo menos uma fonte por período quando houver documento elegível suficiente.
- O sistema extrai e expõe métricas canônicas com evidência auditável.
- O sistema diferencia claramente ausência de cobertura, valor ausente e métrica inexistente.
- O sistema suporta pelo menos dois layouts diferentes sem depender de coordenadas fixas.
- O sistema consegue responder `GET /api/conjuntura?empresa=<slug>&ano=<ano>&trimestre=<tri>` com coleção de métricas canônicas ou estado explícito de ausência de cobertura.

## Próximos artefatos de especificação

- Spec de contratos da API.
- Spec do schema do `Contrato Semântico`.
- Spec do fluxo de ingestão e estados do documento.
- Spec do catálogo inicial de métricas habitacionais.
