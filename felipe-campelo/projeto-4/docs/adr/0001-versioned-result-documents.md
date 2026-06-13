# Version `Documento de Resultado` records by content within the same reporting period

For the same `Empresa` and `Período de Referência`, a republished file with different content is retained as a new `Versão de Documento` instead of overwriting the previous one. We chose this because the challenge requires lineage and idempotence, and content-based version history preserves auditability while still allowing the system to re-evaluate which document is the `Fonte Canônica`.
