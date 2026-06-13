# Spec 0005: Catálogo Inicial de Métricas Habitacionais

Esta especificação define o `Catálogo de Métricas` inicial da v1. Ela determina quais métricas entram na `Superfície Canônica`, como devem ser nomeadas, quais unidades canônicas usam e quais aliases iniciais a `Normalização Semântica` deve reconhecer.

## Objetivos

- Fixar a cobertura mínima da v1.
- Evitar nomes livres na API principal.
- Dar base concreta para `Canonização` e testes.
- Delimitar o que entra como `Métrica` canônica e o que permanece `Métrica Candidata`.

## Princípios

- O catálogo é extensível, mas a v1 começa com um conjunto fechado inicial.
- O `Boletim de Conjuntura` orienta a cobertura mínima, sem ser a única fonte de expansão.
- O nome canônico de API deve ser estável.
- O `Valor Absoluto` é sempre prioritário ao comparativo percentual.
- A mesma métrica pode existir em múltiplos `Recortes de Métrica`.

## Categorias da v1

Valores permitidos para `category`:

- `operacional_comercial`
- `estoque`
- `lancamentos`
- `terrenos`
- `unidades`

## Catálogo inicial

### 1. `vendas-liquidas`

- `name`: `Vendas Líquidas`
- `category`: `operacional_comercial`
- `canonical_unit`: `brl`
- `description`: valor monetário de vendas líquidas do período

Aliases iniciais:

- `vendas liquidas`
- `venda líquida`
- `net sales`
- `vendas contratadas` somente quando a `Normalização Semântica` confirmar equivalência no documento

### 2. `vso`

- `name`: `VSO`
- `category`: `operacional_comercial`
- `canonical_unit`: `percentage`
- `description`: velocidade de vendas reportada para o período

Aliases iniciais:

- `vso`
- `velocidade de vendas`
- `sales over supply`

### 3. `lancamentos-valor`

- `name`: `Lançamentos`
- `category`: `lancamentos`
- `canonical_unit`: `brl`
- `description`: valor monetário total de lançamentos no período

Aliases iniciais:

- `lançamentos`
- `lancamentos`
- `gross launches`
- `psv lançado`
- `valor de lançamentos`

### 4. `lancamentos-unidades`

- `name`: `Unidades Lançadas`
- `category`: `lancamentos`
- `canonical_unit`: `units`
- `description`: quantidade de unidades lançadas no período

Aliases iniciais:

- `unidades lançadas`
- `qtd lançada`
- `launch units`

### 5. `estoque-valor`

- `name`: `Estoque`
- `category`: `estoque`
- `canonical_unit`: `brl`
- `description`: valor monetário do estoque reportado

Aliases iniciais:

- `estoque`
- `inventory`
- `estoque a valor de mercado` quando semanticamente equivalente

### 6. `estoque-unidades`

- `name`: `Unidades em Estoque`
- `category`: `estoque`
- `canonical_unit`: `units`
- `description`: quantidade de unidades em estoque

Aliases iniciais:

- `unidades em estoque`
- `estoque em unidades`
- `inventory units`

### 7. `unidades-vendidas`

- `name`: `Unidades Vendidas`
- `category`: `unidades`
- `canonical_unit`: `units`
- `description`: quantidade de unidades vendidas no período

Aliases iniciais:

- `unidades vendidas`
- `sales units`
- `qtd vendida`

### 8. `unidades-repassadas`

- `name`: `Unidades Repassadas`
- `category`: `unidades`
- `canonical_unit`: `units`
- `description`: quantidade de unidades repassadas/entregues ao financiamento quando reportado

Aliases iniciais:

- `repasses`
- `unidades repassadas`
- `units transferred`

### 9. `banco-de-terrenos-valor`

- `name`: `Banco de Terrenos`
- `category`: `terrenos`
- `canonical_unit`: `brl`
- `description`: valor monetário do landbank reportado

Aliases iniciais:

- `banco de terrenos`
- `landbank`
- `land bank`

### 10. `banco-de-terrenos-potencial`

- `name`: `Potencial do Banco de Terrenos`
- `category`: `terrenos`
- `canonical_unit`: `units`
- `description`: potencial reportado do landbank em unidades, quando a empresa reportar nessa forma

Aliases iniciais:

- `potencial do banco de terrenos`
- `landbank potential`
- `potencial em unidades`

## Métricas fora da superfície canônica inicial

As seguintes famílias não entram na API principal da v1, salvo futura expansão explícita do catálogo:

- EBITDA
- lucro líquido
- margem bruta
- alavancagem
- despesa financeira
- dívida líquida
- guidance narrativo

Essas ocorrências podem ser extraídas como `Métrica Candidata`, mas não devem ser canonizadas na v1.

## Unidades canônicas permitidas

Valores permitidos na v1:

- `brl`
- `units`
- `percentage`
- `percentage_points`

Regras:

- métricas monetárias usam `brl`
- quantidades usam `units`
- métricas percentuais como `VSO` usam `percentage`
- comparativos do tipo `+2,1 p.p.` usam `percentage_points` apenas como comparativo, salvo futura inclusão explícita de métrica primária nessa unidade

## Recortes esperados na v1

Dimensões canônicas iniciais:

- `escopo`
- `regiao`
- `segmento`
- `produto`

Valores canônicos iniciais mínimos:

- `escopo=consolidado`

Outros valores de recorte podem existir na v1 se forem normalizados com segurança.

## Regras de canonização do catálogo

Uma extração só vira `Métrica` canônica se:

- o nome reportado puder ser mapeado para um item deste catálogo;
- a unidade principal for compatível com a métrica canônica;
- os recortes materiais puderem ser normalizados;
- não houver `Mudança de Significado` bloqueante.

Caso contrário:

- o fato vira `Métrica Candidata`; ou
- ocorre `Falha de Canonização`, conforme o caso.

## Ambiguidades tratadas explicitamente

### `Lançamentos`

`Lançamentos` isolado é ambíguo entre valor monetário e quantidade de unidades.

Regra:

- se o contexto ou a unidade apontar para dinheiro, mapear para `lancamentos-valor`
- se apontar para quantidade, mapear para `lancamentos-unidades`
- se não der para decidir com segurança, manter como `Métrica Candidata`

### `Estoque`

`Estoque` isolado também é ambíguo entre valor monetário e unidades.

Aplicar a mesma regra usada para lançamentos.

### `Vendas Contratadas`

Não é alias automático de `Vendas Líquidas`.

Regra:

- só mapear se a `Normalização Semântica` daquele contexto confirmar equivalência
- na dúvida, tratar como `Métrica Candidata`

## Regras para comparativos

Comparativos como:

- `YoY`
- `QoQ`
- `T/T`
- `A/A`
- `p.p.`

não definem a métrica principal. Eles devem ser anexados como informação auxiliar do fato extraído, nunca substituir o item canônico do catálogo.

## Defaults de implementação

- O catálogo deve ser persistido com `slug`, `name`, `category`, `canonical_unit`, `aliases`, `active`.
- A `Normalização Semântica` deve consultar primeiro o catálogo explícito e só depois regras heurísticas.
- Métrica nova fora do catálogo não deve ser exposta pela API principal.
- Expansões futuras do catálogo devem criar nova spec ou atualizar esta com versionamento claro.

## Critérios de aceitação

- A API principal só expõe métricas deste catálogo inicial.
- O pipeline consegue normalizar aliases comuns para o nome canônico correto.
- Ambiguidades entre valor monetário e unidades não são resolvidas por chute.
- Métricas financeiras fora do escopo não vazam para a `Superfície Canônica`.
- `VSO`, `Vendas Líquidas`, `Lançamentos`, `Estoque`, `Unidades` e `Banco de Terrenos` possuem tratamento canônico inicial claro.
