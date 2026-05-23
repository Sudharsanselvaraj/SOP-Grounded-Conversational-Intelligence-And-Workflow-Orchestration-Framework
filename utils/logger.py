"""Structured JSONL logging for the conversation workflow."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from config.settings import LOG_PATH


class JsonLineFormatter(logging.Formatter):
    """Serialize structured payloads as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = getattr(record, "payload", None)
        if isinstance(payload, dict):
            payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            payload.setdefault("level", record.levelname)
            return json.dumps(payload, ensure_ascii=False)

        fallback = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(fallback, ensure_ascii=False)


LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("closira")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    console_handler.setLevel(logging.WARNING)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def log_turn(
    user_message: str,
    ai_response: str,
    confidence: float | None = None,
    escalation_reason: str | None = None,
) -> None:
    """Log one conversational exchange."""

    logger.info(
        "turn",
        extra={
            "payload": {
                "event": "conversation_turn",
                "user_message": user_message,
                "ai_response": ai_response,
                "confidence": confidence,
                "escalation_reason": escalation_reason,
            }
        },
    )


def log_event(event_type: str, detail: dict) -> None:
    """Log a structured event such as escalation, lead capture, or summary generation."""

    logger.info(
        event_type,
        extra={
            "payload": {
                "event": event_type,
                **detail,
            }
        },
    )
