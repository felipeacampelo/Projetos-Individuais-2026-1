from __future__ import annotations


class DocumentPrecedencePolicy:
    PRIORITY = {
        "previa_operacional": 0,
        "apresentacao_resultados": 1,
        "documento_resultado_trimestral": 2,
    }

    def priority_for(self, document_type: str | None) -> int:
        if document_type is None:
            return 999
        return self.PRIORITY.get(document_type.strip().lower(), 999)

    def should_replace(self, current_document_type: str | None, new_document_type: str | None) -> bool:
        return self.priority_for(new_document_type) < self.priority_for(current_document_type)
