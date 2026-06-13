# Spec 0007: Backlog de Implementação da V1

Esta especificação converte as specs anteriores em um backlog executável. O objetivo é permitir implementação incremental, com validação frequente e sem decisões arquiteturais pendentes.

## Princípios

- Cada tarefa deve produzir um artefato verificável.
- O sistema deve ficar executável cedo, mesmo incompleto.
- As dependências entre tarefas devem ser explícitas.
- Sempre priorizar trilha auditável e contratos estáveis antes de “inteligência”.

## Definição de pronto global

Uma tarefa está pronta quando:

- o código compila ou executa no contexto esperado;
- testes mínimos do escopo passam;
- nenhum contrato público daquela tarefa fica implícito;
- observabilidade mínima do fluxo tocado foi adicionada.

## Milestone 1: Fundação da aplicação

Objetivo:

- levantar o esqueleto executável do serviço
- permitir crescimento controlado

### Tarefa 1.1

Criar estrutura de diretórios conforme a `Spec 0006`.

Entregáveis:

- `src/app/main.py`
- `src/app/config.py`
- diretórios vazios principais com `__init__.py`

Critério de pronto:

- a aplicação FastAPI sobe sem erro

### Tarefa 1.2

Implementar configuração tipada por ambiente.

Entregáveis:

- classe `Settings`
- leitura de variáveis de ambiente essenciais

Campos mínimos:

- `app_env`
- `database_url`
- `llm_provider`
- `llm_api_key`
- `polling_enabled`

Critério de pronto:

- settings carregam e validam

### Tarefa 1.3

Implementar `GET /health`.

Entregáveis:

- router `health.py`
- registro do router no app

Critério de pronto:

- endpoint responde `200` com shape da `Spec 0002`

## Milestone 2: Persistência base

Objetivo:

- preparar banco, sessão e migrações

### Tarefa 2.1

Configurar SQLAlchemy base e session management.

Entregáveis:

- `db/base.py`
- `db/session.py`

Critério de pronto:

- sessão cria conexão válida

### Tarefa 2.2

Configurar Alembic.

Entregáveis:

- diretório de migrações
- configuração inicial

Critério de pronto:

- migração vazia roda com sucesso

### Tarefa 2.3

Criar modelos persistidos básicos:

- `Company`
- `CompanyAlias`
- `PublicationSource`
- `MetricCatalogItem`
- `MetricCatalogAlias`

Critério de pronto:

- primeira migração estrutural aplicada

## Milestone 3: Seeds mínimos

Objetivo:

- tornar o domínio consultável cedo

### Tarefa 3.1

Criar seed de empresas iniciais.

Empresas mínimas:

- `mrv`
- `direcional`

Critério de pronto:

- dados carregáveis idempotentemente

### Tarefa 3.2

Criar seed do catálogo inicial conforme `Spec 0005`.

Critério de pronto:

- todos os slugs e aliases iniciais persistidos

### Tarefa 3.3

Implementar:

- `GET /api/companies`
- `GET /api/metricas`

Critério de pronto:

- endpoints respondem com dados seeded

## Milestone 4: Infra de monitoramento

Objetivo:

- permitir jobs de monitoramento e registro de sinais

### Tarefa 4.1

Criar modelos:

- `MonitoringJob`
- `PublicationSignal`

Critério de pronto:

- migração aplicada

### Tarefa 4.2

Implementar `source_registry`.

Responsabilidades:

- listar fontes ativas por empresa
- ordenar por prioridade

Critério de pronto:

- serviço retorna fontes esperadas por empresa

### Tarefa 4.3

Implementar descoberta HTML simples com `httpx + BeautifulSoup`.

Escopo:

- páginas estáticas primeiro

Critério de pronto:

- extrai ao menos um `Sinal de Publicação` sintético a partir de fixture HTML

### Tarefa 4.4

Persistir `MonitoringJob` e `PublicationSignal`.

Critério de pronto:

- job manual grava sinais em banco

## Milestone 5: Recuperação e identidade do documento

Objetivo:

- transformar sinal em documento deduplicável

### Tarefa 5.1

Criar modelos:

- `ResultDocument`
- `DocumentDiscoveryLink`

Critério de pronto:

- migração aplicada

### Tarefa 5.2

Implementar downloader de documento.

Responsabilidades:

- seguir redirecionamento
- baixar conteúdo
- identificar falha de recuperação

Critério de pronto:

- fixture de URL/PDF gera conteúdo bruto ou falha rastreável

### Tarefa 5.3

Implementar cálculo de `sha256` e deduplicação por hash.

Critério de pronto:

- mesmo arquivo com URLs diferentes gera um único `ResultDocument`

### Tarefa 5.4

Persistir `Histórico de Descoberta`.

Critério de pronto:

- múltiplos sinais podem apontar para o mesmo documento

## Milestone 6: Lifecycle de documento

Objetivo:

- dar estados explícitos ao documento

### Tarefa 6.1

Adicionar enum e transições de estado do documento.

Estados mínimos:

- `signal_detected`
- `recovery_failed`
- `content_recovered`
- `duplicate_content`
- `observed`

Critério de pronto:

- transições inválidas são bloqueadas no serviço

### Tarefa 6.2

Criar `DocumentVersionGroup` e `DocumentVersion`.

Critério de pronto:

- documento novo com mesmo empresa+período entra como nova versão, não sobrescreve anterior

## Milestone 7: Parsing bruto de PDF

Objetivo:

- preparar material para extração semântica

### Tarefa 7.1

Implementar parser base com `PyMuPDF`.

Saída mínima:

- texto por página
- metadado de número de página

Critério de pronto:

- fixtures PDF viram páginas textuais persistíveis em memória

### Tarefa 7.2

Implementar heurística de escolha:

- `full scan` para documento curto
- chunking para documento longo

Critério de pronto:

- regra determinística baseada em páginas e volume textual

### Tarefa 7.3

Implementar seleção de páginas/trechos candidatos.

Critério de pronto:

- páginas com termos do catálogo são priorizadas

## Milestone 8: Contrato semântico

Objetivo:

- blindar a saída da extração

### Tarefa 8.1

Implementar schemas Pydantic da `Spec 0003`.

Critério de pronto:

- exemplos da spec validam

### Tarefa 8.2

Criar modelos persistidos:

- `ExtractionRun`
- `CandidateFact`
- `CandidateFactCut`
- `ExtractionEvidence`

Critério de pronto:

- migração aplicada

### Tarefa 8.3

Implementar adaptador de LLM atrás de interface própria.

Critério de pronto:

- a aplicação consegue trocar provedor sem mudar domínio

### Tarefa 8.4

Persistir payload bruto validado do contrato.

Critério de pronto:

- cada extração guarda `contract_version` e payload JSON

## Milestone 9: Canonização

Objetivo:

- promover fatos candidatos para métricas canônicas

### Tarefa 9.1

Implementar normalização de empresa e aliases.

Critério de pronto:

- `MRV`, `MRV&CO` e aliases seeded convergem para `mrv`

### Tarefa 9.2

Implementar normalização de métricas conforme `Spec 0005`.

Critério de pronto:

- aliases conhecidos resolvem para o slug correto

### Tarefa 9.3

Implementar normalização de unidade.

Critério de pronto:

- `R$ milhões` e `R$ mil` viram `brl` com escala correta

### Tarefa 9.4

Implementar normalização de recortes.

Critério de pronto:

- `consolidado` vira `escopo=consolidado`

### Tarefa 9.5

Implementar políticas:

- `EvidencePrecedencePolicy`
- `DocumentPrecedencePolicy`
- `SemanticCompletenessEvaluator`
- `MeaningChangeGuard`

Critério de pronto:

- unit tests cobrem cada política

### Tarefa 9.6

Criar modelos:

- `CanonicalMetric`
- `CanonicalMetricCut`
- `NormalizationKnowledgeVersion`

Critério de pronto:

- migração aplicada

### Tarefa 9.7

Implementar `ReevaluateCanonicalSourceService`.

Critério de pronto:

- nova versão pode substituir documento canônico e mover o anterior para `superseded`

## Milestone 10: API canônica

Objetivo:

- expor conjuntura com semântica explícita

### Tarefa 10.1

Implementar schemas públicos da API.

Critério de pronto:

- responses seguem `Spec 0002`

### Tarefa 10.2

Implementar `QueryConjunturaService`.

Critério de pronto:

- responde métricas canônicas por empresa, ano e trimestre

### Tarefa 10.3

Implementar `GET /api/conjuntura`.

Critério de pronto:

- diferencia `coverage.available` de `coverage.unavailable`

### Tarefa 10.4

Implementar `GET /api/documentos`.

Critério de pronto:

- mostra estados e canonicidade do documento

### Tarefa 10.5

Implementar `POST /api/ingest/run`.

Critério de pronto:

- aceita escopo e retorna `job_id`

## Milestone 11: Scheduler e reprocessamento

Objetivo:

- automatizar o pipeline contínuo

### Tarefa 11.1

Integrar `APScheduler`.

Critério de pronto:

- job periódico dispara monitoramento

### Tarefa 11.2

Implementar reprocessamento por gatilho material.

Critério de pronto:

- alteração de versão de contrato ou conhecimento de normalização cria elegibilidade de reprocessamento

### Tarefa 11.3

Implementar proteção contra reprocessamento cego.

Critério de pronto:

- conteúdo idêntico sem mudança material não volta ao LLM

## Milestone 12: Observabilidade e robustez

Objetivo:

- tornar falhas explicáveis e o sistema demonstrável

### Tarefa 12.1

Adicionar logging estruturado com correlação.

Chaves mínimas:

- `job_id`
- `signal_id`
- `document_id`
- `extraction_id`

### Tarefa 12.2

Registrar motivos explícitos de:

- `Falha de Recuperação`
- `Falha de Interpretação`
- `Falha de Canonização`

### Tarefa 12.3

Criar fixtures finais de dois layouts diferentes.

Critério de pronto:

- os dois cenários entram no pipeline com trilha auditável completa

## Sequência mínima para demo funcional

Se o tempo apertar, a ordem mínima de entrega deve ser:

1. Milestones 1, 2 e 3
2. Milestones 4, 5 e 6
3. Milestones 7 e 8
4. Milestones 9 e 10
5. Milestone 12
6. Milestone 11 por último, se necessário

Motivo:

- o scheduler contínuo pode ficar por último sem comprometer a prova de conceito do pipeline;
- já a trilha de documento, extração e canonização é central para o desafio.

## Critérios de aceite final da v1

- duas empresas monitoradas
- pelo menos dois layouts processados
- deduplicação por hash funcionando
- versionamento de documento funcionando
- extração validada por contrato versionado
- canonização para catálogo inicial funcionando
- `GET /api/conjuntura` funcional com cobertura explícita
- `GET /api/documentos` funcional para auditoria
- evidência de origem preservada por métrica
