import contextvars
import json
import logging
import time
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.configs.settings import get_settings


request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

LOGGER_NAME = "ai_short_drama"
_HANDLER_MARKER = "_ai_short_drama_jsonl_handler"


class JsonLineFormatter(logging.Formatter):
    """Format structured log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = record.msg if isinstance(record.msg, dict) else {}
        if not isinstance(payload, dict):
            payload = {}

        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "request_id": get_request_id(),
            **_sanitize(payload),
        }
        if record.exc_info:
            log_record["error_type"] = record.exc_info[0].__name__
        return json.dumps(log_record, ensure_ascii=False, separators=(",", ":"))


def configure_logging(log_file_path: str | None = None) -> None:
    """Configure local JSONL logging once, replacing any previous JSONL handler."""

    settings = get_settings()
    path = Path(log_file_path or settings.log_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.close()

    handler = logging.FileHandler(path, encoding="utf-8")
    setattr(handler, _HANDLER_MARKER, True)
    handler.setFormatter(JsonLineFormatter())
    logger.addHandler(handler)


def get_request_id() -> str | None:
    return request_id_var.get()


def set_request_id(request_id: str | None = None) -> contextvars.Token[str | None]:
    return request_id_var.set(request_id or str(uuid.uuid4()))


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    request_id_var.reset(token)


def log_event(event: str, level: str = "info", **fields: Any) -> None:
    """Emit one structured event. Only allowlisted, JSON-safe fields are logged."""

    logger = logging.getLogger(LOGGER_NAME)
    if not any(getattr(handler, _HANDLER_MARKER, False) for handler in logger.handlers):
        configure_logging()

    payload = {"event": event, **fields}
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(numeric_level, payload)


def read_recent_logs(
    project_id: int | None = None,
    limit: int = 200,
    log_file_path: str | None = None,
) -> list[dict[str, Any]]:
    """Read recent JSONL log records for the dev-only diagnostics endpoint."""

    settings = get_settings()
    path = Path(log_file_path or settings.log_file_path)
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if project_id is not None and record.get("project_id") != project_id:
            continue
        records.append(record)
    return records[-limit:]


def request_id() -> str:
    return get_request_id() or str(uuid.uuid4())


def duration_ms(started_at: float) -> int:
    return round((time.perf_counter() - started_at) * 1000)


def _sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize(item)
            for key, item in value.items()
            if _safe_field_name(str(key))
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value[:50]]
    if isinstance(value, tuple | set):
        return [_sanitize(item) for item in list(value)[:50]]
    if isinstance(value, int | float | bool) or value is None:
        return value
    if isinstance(value, str):
        return value[:500]
    return str(value)[:500]


def _safe_field_name(name: str) -> bool:
    blocked = ("api_key", "token", "secret", "password", "prompt", "script")
    return not any(blocked_item in name.lower() for blocked_item in blocked)

