# Spec 0004: Fluxo de Ingestão e Ciclo de Vida do Documento

Esta especificação define como o sistema monitora `Fontes de Publicação`, transforma `Sinais de Publicação` em `Documentos Observados`, evita duplicidade, versiona conteúdo e conduz documentos até a `Canonização` ou falha recuperável.

## Objetivos

- Tornar o fluxo contínuo e idempotente.
- Separar descoberta, recuperação, interpretação e canonização.
- Preservar auditabilidade desde o primeiro sinal até a decisão final.
- Definir estados e transições implementáveis do documento.

## Escopo da v1

- Polling agendado como mecanismo primário de `Monitoramento de Fonte`.
- Suporte a múltiplas `Fontes de Publicação` por `Empresa`.
- Idempotência por `Identidade do Documento` baseada em hash de conteúdo.
- Histórico de `Versões de Documento` no mesmo `Período de Referência`.
- `Reprocessamento` dirigido por mudança material, não por repetição cega.

## Unidades do fluxo

### Job de monitoramento

Execução agendada que percorre uma ou mais `Fontes de Publicação`.

Cada job possui:

- `job_id`
- `started_at`
- `finished_at`
- `scope`
- `status`

### Sinal de Publicação

Artefato preliminar descoberto no job. Deve registrar:

- empresa alvo
- fonte de publicação
- URL ou referência do item encontrado
- texto âncora ou título
- timestamp da descoberta

### Documento Observado

Só existe depois que houve recuperação de conteúdo suficiente para calcular `Identidade do Documento` e iniciar interpretação.

## Fluxo de ponta a ponta

### 1. Seleção de fontes

Cada job de monitoramento seleciona as `Fontes de Publicação` ativas por `Prioridade de Fonte`.

Regra da v1:

- a ordem de prioridade influencia a ordem de tentativa de descoberta;
- ela não altera `Identidade do Documento`;
- ela não define sozinha `Fonte Canônica`.

### 2. Descoberta de sinais

Para cada fonte:

- carregar a página, feed ou listagem;
- identificar itens com potencial de apontar para `Documento de Resultado`;
- gerar zero ou mais `Sinais de Publicação`.

Um `Sinal de Publicação` ainda não é documento. Ele precisa ser tentado para recuperação.

### 3. Recuperação de conteúdo

Para cada sinal:

- seguir o link primário;
- resolver redirecionamentos;
- baixar o PDF ou artefato equivalente;
- validar que há conteúdo recuperável.

Resultados possíveis:

- conteúdo recuperado com sucesso;
- `Falha de Recuperação` se não houver conteúdo recuperável.

Se a recuperação falhar:

- o sinal continua registrado;
- nenhum `Documento Observado` é criado;
- o item fica elegível para `Reprocessamento` posterior quando houver novo `Gatilho de Reprocessamento`.

### 4. Identidade e deduplicação

Após recuperar o arquivo:

- calcular hash `sha256` do conteúdo bruto;
- registrar tamanho do arquivo e URL final efetiva;
- procurar documento existente com o mesmo hash.

Regras:

- mesmo hash em URLs diferentes: mesmo documento;
- mesma URL com hash diferente: novo documento;
- hash novo para mesma empresa e mesmo período: nova `Versão de Documento` potencial, não duplicata.

### 5. Registro do Documento Observado

Quando o conteúdo é novo:

- criar `Documento Observado`;
- vincular `Histórico de Descoberta`;
- registrar hash, URLs, timestamps e metadados técnicos.

Quando o conteúdo já existe:

- anexar o novo `Sinal de Publicação` ao `Histórico de Descoberta`;
- não chamar o LLM novamente;
- encerrar o item como duplicado observado.

### 6. Parsing preliminar

Para cada `Documento Observado` novo:

- extrair texto bruto com parser de PDF;
- segmentar por página;
- identificar páginas e trechos candidatos.

Se o parsing bruto não produzir conteúdo útil:

- registrar `Falha de Interpretação`;
- manter o documento no histórico como observado;
- permitir reprocessamento posterior.

### 7. Extração estruturada

Aplicar o `Contrato Semântico` versionado à interpretação do documento.

Resultados possíveis:

- extração validada no schema;
- `Falha de Interpretação` se o objeto não validar ou se não houver estrutura mínima.

### 8. Normalização e canonização

Sobre os fatos candidatos extraídos:

- resolver empresa;
- resolver período;
- normalizar métricas, unidades e recortes;
- aplicar `Precedência de Evidência`;
- avaliar `Completude Semântica`;
- detectar `Mudança de Significado`.

Resultados possíveis:

- documento vira `Fonte Canônica`;
- documento permanece `Documento Observado` não canônico;
- fatos viram `Métrica Candidata`;
- ocorre `Falha de Canonização`.

### 9. Reavaliação da Fonte Canônica

Se o documento pertence a uma empresa e período que já possuem `Fonte Canônica`:

- comparar tipo de documento;
- comparar elegibilidade;
- comparar completude semântica;
- comparar eventuais conflitos de significado.

Regras:

- `Prévia Operacional` tem precedência sobre outros documentos elegíveis;
- nova versão não substitui automaticamente a anterior;
- a troca exige `Reavaliação de Fonte Canônica`.

## Estados do documento

Os estados abaixo são estados persistidos do ciclo de vida lógico do documento.

### Estados da v1

- `signal_detected`
- `recovery_failed`
- `content_recovered`
- `duplicate_content`
- `observed`
- `interpretation_failed`
- `extracted`
- `canonicalization_failed`
- `canonical`
- `superseded`

## Semântica de cada estado

### `signal_detected`

- existe `Sinal de Publicação`
- ainda não existe `Documento Observado`

### `recovery_failed`

- houve tentativa de recuperação
- não houve conteúdo suficiente para formar `Documento Observado`

### `content_recovered`

- arquivo recuperado com sucesso
- hash calculado
- deduplicação ainda não concluída ou acabou de concluir

### `duplicate_content`

- hash já conhecido
- novo processamento semântico não ocorre
- apenas o `Histórico de Descoberta` é enriquecido

### `observed`

- documento novo identificado
- apto a seguir para parsing e interpretação

### `interpretation_failed`

- parsing bruto ou `Extração` não produziram saída válida

### `extracted`

- houve saída válida no `Contrato Semântico`
- ainda não houve decisão final de canonização

### `canonicalization_failed`

- houve extração válida
- faltou normalização, completude ou resolução semântica suficiente

### `canonical`

- o documento é a `Fonte Canônica` atual para empresa e período

### `superseded`

- o documento já foi canônico ou elegível relevante
- deixou de ser a `Fonte Canônica` após reavaliação por versão melhor ou documento prioritário

## Transições permitidas

### Caminho principal

- `signal_detected -> content_recovered`
- `content_recovered -> duplicate_content`
- `content_recovered -> observed`
- `observed -> extracted`
- `extracted -> canonical`

### Caminhos de falha

- `signal_detected -> recovery_failed`
- `observed -> interpretation_failed`
- `extracted -> canonicalization_failed`

### Caminhos de reavaliação

- `canonical -> superseded`
- `canonicalization_failed -> extracted`
- `interpretation_failed -> observed`
- `recovery_failed -> signal_detected`

Não é permitido:

- `duplicate_content -> canonical`
- `recovery_failed -> canonical`
- `signal_detected -> canonical`

## Regras de idempotência

- O mesmo hash nunca deve disparar nova extração semântica na mesma versão de conhecimento.
- Descobertas repetidas do mesmo hash apenas enriquecem trilha de descoberta.
- `force_reprocess` não quebra a regra de identidade; ele atua sobre itens elegíveis por estado e gatilho, não sobre duplicatas perfeitas já canônicas sem mudança material.

## Regras de versionamento do documento

Quando um novo hash cair no mesmo `Empresa + Período de Referência`:

- criar nova `Versão de Documento`;
- manter vínculo com o mesmo agrupamento lógico do período;
- executar fluxo completo de interpretação e canonização;
- decidir se a nova versão:
  - vira `canonical`
  - permanece `observed`
  - termina como `canonicalization_failed`

Se a nova versão vencer:

- a anterior vai para `superseded`

## Gatilhos de reprocessamento

Um item só deve ser reprocessado se houver `Gatilho de Reprocessamento` material:

- nova versão do documento;
- conteúdo antes indisponível agora recuperável;
- nova versão do `Contrato Semântico`;
- nova versão do `Conhecimento de Normalização`;
- melhoria comprovada do mecanismo de interpretação.

## Metadados mínimos persistidos por documento

- `document_id`
- `company_slug` quando resolvido
- `source_urls`
- `source_priority_at_discovery`
- `content_hash`
- `first_seen_at`
- `last_seen_at`
- `published_at` quando disponível
- `reference_period` quando resolvido
- `document_type` quando resolvido
- `current_state`
- `canonical_for_scope` booleano
- `superseded_by_document_id` opcional
- `contract_version_used` opcional
- `normalization_version_used` opcional

## Regras de observabilidade

Cada job e cada documento devem permitir responder:

- de qual fonte veio;
- quando foi visto pela primeira vez;
- por que não virou canônico, se não virou;
- qual versão de contrato e conhecimento semântico foi usada;
- qual documento é a `Fonte Canônica` atual por empresa e período.

## Critérios de aceitação

- O pipeline registra `Sinais de Publicação` separadamente de `Documentos Observados`.
- O sistema não reprocessa conteúdo idêntico já conhecido.
- O sistema preserva histórico de `Versões de Documento`.
- O sistema modela falhas de recuperação, interpretação e canonização de forma distinta.
- O sistema permite reprocessamento apenas por mudança material.
- O sistema consegue promover e substituir `Fonte Canônica` sem perda de linhagem.
