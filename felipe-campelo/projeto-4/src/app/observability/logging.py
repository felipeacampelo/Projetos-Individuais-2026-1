from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class LogContext:
    job_id: str | None = None
    signal_id: str | None = None
    document_id: str | None = None
    extraction_id: str | None = None
    extra: dict[str, object] = field(default_factory=dict)


class StructuredLogger:
    def __init__(self, name: str = "pipeline_uda") -> None:
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, message: str, context: LogContext | None = None) -> None:
        self._emit("info", message, context)

    def error(self, message: str, context: LogContext | None = None) -> None:
        self._emit("error", message, context)

    def _emit(self, level: str, message: str, context: LogContext | None) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        if context is not None:
            payload.update(
                {
                    "job_id": context.job_id,
                    "signal_id": context.signal_id,
                    "document_id": context.document_id,
                    "extraction_id": context.extraction_id,
                }
            )
            payload.update(context.extra)
        self.logger.log(logging.INFO if level == "info" else logging.ERROR, json.dumps(payload))
