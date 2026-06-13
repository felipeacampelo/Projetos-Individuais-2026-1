# Pipeline UDA de RI Habitacional

Glossary for the pipeline that monitors investor-relations publications from homebuilding companies, extracts quarterly operating metrics, and serves structured conjuncture data.

## Language

**Documento de Resultado**:
A quarterly investor-relations source document published by a company that may contain operating or market metrics relevant to the pipeline.
_Avoid_: relatório, PDF, arquivo, boletim

**Prévia Operacional**:
A subtype of Documento de Resultado and the preferred source for metric extraction when it exists for a given company and quarter.
_Avoid_: relatório operacional, release

**Boletim de Conjuntura**:
A downstream analytical artifact that consumes structured extracted data and serves as the minimum coverage reference for the v1 domain, but it is not a primary source for ingestion or the sole authority over the metric catalog.
_Avoid_: fonte, relatório-fonte

**Período de Referência**:
The canonical quarter and year explicitly declared by a Documento de Resultado; publication date is metadata and never the source of truth for the reporting period.
_Avoid_: trimestre de publicação, data-base

**Fonte Canônica**:
The single Documento de Resultado selected as the authoritative source for one company in one Período de Referência, with Prévia Operacional taking precedence when available.
_Avoid_: fonte principal, documento preferido

**Métrica**:
A structured reported fact extracted from a Fonte Canônica for one company and one Período de Referência, identified by a canonical name, a value, an explicit unit, a normalized scale when applicable, and a business cut that may be explicit consolidated scope, region, segment, or product line.
_Avoid_: indicador, número, campo

**Valor Absoluto**:
The primary reported value for a Métrica in the canonical dataset, used in preference to any comparative percentage or growth rate presented alongside it.
_Avoid_: variação, percentual, destaque de marketing

**Escala Monetária Canônica**:
The internal normalization of monetary Métricas to absolute reais, while preserving the originally reported unit and scale in the Evidência de Extração.
_Avoid_: valor monetário em escala arbitrária, unidade implícita

**Unidade Canônica**:
The semantically precise measurement unit associated with a Métrica, preserving distinctions such as percentage versus percentage points rather than collapsing them into a generic numeric type.
_Avoid_: número sem unidade, percentual genérico

**Recorte de Métrica**:
The normalized business cut associated with a Métrica, represented canonically as a typed dimension and a normalized value rather than as free text, with aliases resolved before canonical exposure.
_Avoid_: label solta, string ambígua

**Materialidade do Recorte**:
The condition in which a Recorte de Métrica changes the analytical identity of a Métrica and therefore cannot be dropped, left ambiguous, or exposed as raw text in canonical data.
_Avoid_: detalhe cosmético, etiqueta irrelevante

**Composição de Recortes**:
The ability for a single Métrica to carry multiple Recortes de Métrica simultaneously when the source reports intersecting business cuts, with no semantic ordering among them.
_Avoid_: recorte único obrigatório, concatenação textual

**Valor Ausente**:
The explicit absence of a valid Valor Absoluto for a Métrica, represented as null rather than inferred or discarded when the source only provides comparative context.
_Avoid_: zero, estimativa, inferência

**Métrica Inexistente**:
The absence of a canonical metric for a requested scope because that metric was not reported or canonized there, which is distinct from Cobertura Canônica ausente and from Valor Ausente.
_Avoid_: null genérico, falta de cobertura

**Evidência de Extração**:
The auditable link between a Métrica and the exact portion of the Fonte Canônica from which it was derived, including at least the source document, page or section, and supporting text snippet.
_Avoid_: referência, observação, comentário

**Extração**:
The domain step that turns a Documento Observado into structured, auditable candidate facts, including LLM-produced structured output, without deciding by itself what becomes canonical.
_Avoid_: dado canônico automático, interpretação final

**Canonização**:
The domain step that promotes extracted candidate facts into the Superfície Canônica only after semantic normalization, conflict resolution, and completeness checks.
_Avoid_: simples parsing, saída bruta do modelo

**Precedência de Evidência**:
The rule that resolves conflicting values for the same Métrica and business cut inside one Fonte Canônica, prioritizing explicit current-period tables over summaries, prose, and marketing-oriented comparisons.
_Avoid_: desempate ad hoc, escolha manual

**Mudança de Layout**:
A variation in document presentation that preserves the semantic identity of the reported Empresa, Período de Referência, Métricas, Recortes, and Evidências de Extração.
_Avoid_: mudança de significado, variação semântica

**Mudança de Significado**:
A variation in what a reported item means, such that apparently similar document content can no longer be assumed to refer to the same canonical Métrica or Recorte.
_Avoid_: mudança cosmética, simples troca de layout

**Empresa**:
The canonical business entity monitored by the pipeline and exposed by the API, independent of the literal names, brands, or tickers used across investor-relations documents.
_Avoid_: nome do PDF, emissor textual, companhia como string livre

**Slug de Empresa**:
The stable public identifier used to persist and query an Empresa across the system, while document names and tickers remain aliases.
_Avoid_: nome livre, ticker como chave primária

**Catálogo de Métricas**:
The extensible canonical vocabulary of operational and housing-market metric names accepted by the domain, requiring normalization before a metric is exposed through the primary API.
_Avoid_: campo livre, nome cru do documento

**Conhecimento de Normalização**:
The evolving domain knowledge that explains how reported source language maps into canonical metrics, units, cuts, and meanings, distinct from the catalog of canonical concepts itself.
_Avoid_: catálogo implícito, equivalência ad hoc

**Fonte de Verdade Semântica**:
The explicit and centralized domain knowledge that defines canonical meanings and normalization rules, which prompts and extraction mechanisms consume rather than own.
_Avoid_: semântica espalhada, prompt como autoridade

**Normalização Semântica**:
The domain process that maps reported names, units, cuts, and meanings from source documents into canonical concepts before data can be exposed through the Superfície Canônica, and it evolves over time as domain knowledge improves.
_Avoid_: cópia literal, mapeamento implícito

**Contrato Semântico**:
The explicit and versionable structure and validity boundary for extracted candidate facts, enforcing typed output and disciplined absence handling without by itself deciding canonical promotion.
_Avoid_: verdade canônica automática, schema como fim do processo

**Métrica Candidata**:
A metric-shaped extraction that is auditable and persisted internally but is not yet part of the Catálogo de Métricas, or is blocked from canonization by unresolved semantic ambiguity, and therefore is not exposed through the canonical API contract.
_Avoid_: métrica oficial, campo definitivo

**Consulta de Conjuntura**:
The canonical API response shape that returns a collection of normalized Métricas for a requested scope, rather than an ad hoc aggregated summary by document or company.
_Avoid_: resumo fechado, payload agregado por conveniência

**Superfície Canônica**:
The public domain surface that exposes only canonical Métricas derived from a Fonte Canônica, including minimal auditability metadata while excluding operational and provisional records from the primary API.
_Avoid_: mistura com estados internos, API operacional pública

**Cobertura Canônica**:
The explicit domain state that indicates whether a requested scope has canonical data available from a valid Fonte Canônica, distinct from an empty result caused by missing values or nonexistent metrics.
_Avoid_: vazio ambíguo, ausência silenciosa

**Falha de Recuperação**:
The inability to obtain recoverable content from a Sinal de Publicação, preventing the creation of a Documento Observado.
_Avoid_: erro genérico, documento observado sem conteúdo

**Falha de Interpretação**:
The inability to produce a valid structured extraction from a Documento Observado.
_Avoid_: falha técnica genérica, ausência de canonização

**Falha de Canonização**:
The inability to promote an extraction into canonical domain data because of unresolved conflicts, missing normalization, materially ambiguous cuts, or insufficient semantic completeness.
_Avoid_: erro único de processamento, descarte sem motivo

**Reprocessamento**:
The deliberate retry of a previously unsuccessful or provisional domain record after new content, new interpretation capability, or new normalization knowledge becomes available.
_Avoid_: falha terminal, repetição cega

**Gatilho de Reprocessamento**:
A material domain change that justifies a Reprocessamento, such as a new Versão de Documento, improved interpretation capability, new normalization knowledge, or newly recoverable source content.
_Avoid_: reexecução cega, repetição por rotina

**Escopo Temporal Explícito**:
The rule that a Consulta de Conjuntura must be requested with an explicit reporting period scope, rather than implicitly assuming the latest available quarter.
_Avoid_: último trimestre implícito, período automático

**Identidade do Documento**:
The canonical identity of a Documento de Resultado derived from its file content rather than its discovery URL, so that duplicate files collapse and changed files are treated as new documents.
_Avoid_: URL como identidade, nome do arquivo como chave

**Versão de Documento**:
A distinct published content variant of a Documento de Resultado for the same Empresa and Período de Referência, retained in history and eligible to replace the Fonte Canônica.
_Avoid_: sobrescrita silenciosa, correção destrutiva

**Reavaliação de Fonte Canônica**:
The rule that a new Versão de Documento only replaces the current Fonte Canônica after being re-evaluated for eligibility, precedence, and semantic completeness, rather than by recency alone.
_Avoid_: versão mais nova sempre vence, substituição automática

**Completude Semântica**:
The minimum condition for a Documento de Resultado to serve canonically for a period: identifiable Empresa and Período de Referência, at least one extractable canonical Métrica with Evidência de Extração, and no unresolved conflict that blocks canonical selection.
_Avoid_: score arbitrário, checklist rígido de métricas

**Documento Observado**:
A recovered and identifiable Documento de Resultado that remains part of the domain record even when it does not qualify as Fonte Canônica, preserving visibility into unsuccessful or incomplete source candidates.
_Avoid_: descarte silencioso, documento ignorado sem rastro

**Monitoramento de Fonte**:
The continuous domain capability of watching investor-relations publication channels to discover new Documento de Resultado candidates as they appear.
_Avoid_: execução manual, raspagem pontual

**Fonte de Publicação**:
A specific investor-relations publication channel monitored for new Documento de Resultado candidates, such as a results page, downloads listing, or feed associated with one Empresa.
_Avoid_: empresa, site inteiro, URL solta

**Prioridade de Fonte**:
The ordering rule among multiple Fontes de Publicação for the same Empresa, used to prefer more reliable channels during discovery without changing document identity or canonicity by itself.
_Avoid_: fonte única obrigatória, escolha aleatória

**Sinal de Publicação**:
A preliminary discovery cue from a Fonte de Publicação that suggests a new Documento de Resultado may exist, but that is not yet a Documento Observado until recoverable content is obtained.
_Avoid_: documento confirmado, fonte canônica

**Histórico de Descoberta**:
The retained record of one or more Sinais de Publicação that converged into the same Documento Observado.
_Avoid_: primeira URL apenas, descoberta sem trilha
