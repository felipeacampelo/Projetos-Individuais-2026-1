# Spec 0003: Schema do Contrato Semântico

Esta especificação define o `Contrato Semântico` da v1 para a etapa de `Extração`. O objetivo é produzir fatos candidatos estruturados, auditáveis e reprocessáveis, sem confundir schema válido com dado canônico.

## Objetivos

- Blindar a saída estruturada da extração contra formatos livres.
- Tornar ausências explícitas.
- Carregar evidência suficiente para auditoria e canonização posterior.
- Permitir evolução versionada do contrato.

## Princípios

- O contrato é versionável.
- Uma saída válida no contrato continua sendo apenas resultado de `Extração`.
- O contrato aceita fatos candidatos que ainda não sejam canônicos.
- O contrato nunca permite inferência silenciosa de `Valor Absoluto`.
- O contrato deve ser suficientemente rico para suportar `Normalização Semântica`, `Canonização` e `Reprocessamento`.

## Envelope do contrato

Cada extração deve produzir um único objeto com estes campos de topo:

```json
{
  "contract_version": "1.0.0",
  "extraction_id": "ext_01",
  "document": {},
  "facts": [],
  "warnings": []
}
```

## Campo `document`

Representa a identificação mínima do documento interpretado.

```json
{
  "source_url": "https://ri.exemplo.com/3t25.pdf",
  "document_type": "previa_operacional",
  "company_reported_name": "MRV",
  "reference_period": {
    "year": 2025,
    "quarter": 3
  }
}
```

### Regras

- `source_url`: obrigatório.
- `document_type`: obrigatório.
- `company_reported_name`: obrigatório se legível no documento.
- `reference_period.year`: obrigatório.
- `reference_period.quarter`: obrigatório e restrito a `1..4`.

## Campo `facts`

`facts` é a coleção de fatos candidatos extraídos do documento.

Cada item de `facts` deve obedecer ao shape abaixo.

```json
{
  "reported_metric_name": "Vendas Líquidas",
  "candidate_metric_category": "operacional",
  "value_status": "reported",
  "reported_value": 420.0,
  "reported_unit": "R$ milhões",
  "canonical_numeric_value": 420000000.0,
  "canonical_unit_hint": "brl",
  "comparative_values": [
    {
      "kind": "yoy_variation_percentage",
      "value": 18.0,
      "unit": "%"
    }
  ],
  "cuts": [
    {
      "dimension_label": "escopo",
      "value_label": "consolidado",
      "is_material": true
    }
  ],
  "evidence": {
    "page": 7,
    "section": "Destaques Operacionais",
    "snippet": "Vendas líquidas totalizaram R$ 420 milhões no 3T25."
  }
}
```

## Regras de cada fato candidato

### Identidade textual

- `reported_metric_name`: obrigatório.
- `candidate_metric_category`: obrigatório; valores iniciais permitidos:
  - `operacional`
  - `mercado_habitacional`
  - `desconhecida`

### Estado do valor

- `value_status`: obrigatório; valores permitidos:
  - `reported`
  - `missing`

#### Quando `value_status = "reported"`

- `reported_value`: obrigatório.
- `reported_unit`: obrigatório.
- `canonical_numeric_value`: opcional, mas recomendado quando a escala for interpretável já na extração.

#### Quando `value_status = "missing"`

- `reported_value = null`
- `canonical_numeric_value = null`
- `reported_unit` pode existir se a unidade for conhecida pelo contexto

### Comparativos

- `comparative_values` é opcional.
- Nunca substitui o valor principal.
- Cada comparativo deve ter:
  - `kind`
  - `value`
  - `unit`

### Recortes

- `cuts` é opcional, mas quando presente deve ser uma lista de objetos.
- Cada item deve conter:
  - `dimension_label`
  - `value_label`
  - `is_material`

Não é exigido que a normalização do recorte já esteja resolvida aqui. O contrato da extração captura o que foi entendido do documento; a canonização decide se isso sobe.

### Evidência

`evidence` é obrigatória para todo fato candidato.

Campos mínimos:

- `page`: opcional, mas fortemente recomendada
- `section`: opcional
- `snippet`: obrigatório

### Snippet

- deve ser curto, literal e suficiente para auditoria;
- não precisa reproduzir a página inteira;
- deve apontar diretamente para o valor ou contexto que embasa a extração.

## Campo `warnings`

Lista opcional de advertências sem bloquear a validade do contrato.

Exemplos:

- `metric_name_ambiguous`
- `material_cut_not_normalized`
- `comparative_only_context_present`
- `possible_meaning_change`

Shape:

```json
{
  "code": "possible_meaning_change",
  "message": "The document appears to use a different meaning for the reported metric label."
}
```

## Restrições explícitas

O contrato da v1 não permite:

- valor implícito sem `value_status`
- percentual promocional ocupando o lugar do valor principal
- fato sem `reported_metric_name`
- fato sem `evidence.snippet`
- trimestre fora de `1..4`
- ausência silenciosa de informação obrigatória

## Mapeamento para canonização

Um fato candidato pode seguir estes destinos:

- virar `Métrica` canônica
- virar `Métrica Candidata` persistida
- resultar em `Falha de Canonização`

O contrato semântico não decide qual dos três acontecerá.

## Exemplo válido com valor ausente

```json
{
  "contract_version": "1.0.0",
  "extraction_id": "ext_02",
  "document": {
    "source_url": "https://ri.exemplo.com/3t25.pdf",
    "document_type": "apresentacao_resultados",
    "company_reported_name": "MRV",
    "reference_period": {
      "year": 2025,
      "quarter": 3
    }
  },
  "facts": [
    {
      "reported_metric_name": "VSO",
      "candidate_metric_category": "operacional",
      "value_status": "missing",
      "reported_value": null,
      "reported_unit": "%",
      "canonical_numeric_value": null,
      "canonical_unit_hint": "percentage",
      "comparative_values": [
        {
          "kind": "qoq_variation_percentage_points",
          "value": 2.1,
          "unit": "p.p."
        }
      ],
      "cuts": [
        {
          "dimension_label": "escopo",
          "value_label": "consolidado",
          "is_material": true
        }
      ],
      "evidence": {
        "page": 9,
        "section": "Indicadores Comerciais",
        "snippet": "VSO apresentou crescimento de 2,1 p.p. no trimestre."
      }
    }
  ],
  "warnings": [
    {
      "code": "comparative_only_context_present",
      "message": "No absolute reported value was found for the metric."
    }
  ]
}
```

## Defaults de implementação

- O contrato deve ser implementado em Pydantic.
- A extração deve falhar se o objeto não validar.
- O pipeline deve persistir o payload bruto validado junto com a versão do contrato.
- O versionamento inicial é `1.0.0`.
- Mudanças incompatíveis no shape exigem nova major version.
- Mudanças compatíveis por adição opcional podem incrementar minor version.

## Critérios de aceitação

- Toda saída válida possui envelope, documento, fatos e warnings conforme o schema.
- Toda ausência relevante é explicitada, nunca inferida.
- Toda métrica candidata possui evidência auditável.
- O contrato suporta fatos com recortes múltiplos.
- O contrato suporta valores ausentes e comparativos auxiliares sem perder a distinção entre eles.
