"""Structured JSONL run logging for the STS2 MCP bridge."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2026-05-10"

DEFAULT_REDACT_KEY_PARTS = (
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
)


class RunLogger:
    """Append-only JSONL logger with stable event envelopes."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        log_dir: str | os.PathLike[str] = "logs",
        preview_chars: int = 4000,
        include_full_text: bool = False,
        redact_key_parts: tuple[str, ...] = DEFAULT_REDACT_KEY_PARTS,
    ) -> None:
        self.enabled = enabled
        self.log_dir = Path(log_dir)
        self.preview_chars = max(0, preview_chars)
        self.include_full_text = include_full_text
        self.redact_key_parts = tuple(part.lower() for part in redact_key_parts)
        self.run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.path = self.log_dir / f"run_{self.run_id}.jsonl"
        self._sequence = 0
        self._started_at = time.monotonic()
        self._lock = asyncio.Lock()

    def start(self, metadata: dict[str, Any] | None = None) -> None:
        if not self.enabled:
            return

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._write_sync(
            self._envelope(
                "session_start",
                {
                    "log_path": str(self.path),
                    "metadata": self.redact(metadata or {}),
                },
            )
        )

    async def log(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
    ) -> None:
        if not self.enabled:
            return

        async with self._lock:
            record = self._envelope(
                event_type,
                self.redact(payload or {}),
                tool_call_id=tool_call_id,
                tool_name=tool_name,
            )
            self._write_sync(record)

    def redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                if self._is_sensitive_key(key_text):
                    redacted[key_text] = "[REDACTED]"
                else:
                    redacted[key_text] = self.redact(item)
            return redacted
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        if isinstance(value, tuple):
            return [self.redact(item) for item in value]
        return value

    def summarize_text(self, text: str | bytes | None) -> dict[str, Any]:
        if text is None:
            return {"length": 0, "sha256": None, "preview": ""}
        if isinstance(text, bytes):
            raw = text
            display = text.decode("utf-8", errors="replace")
        else:
            display = text
            raw = text.encode("utf-8", errors="replace")

        summary: dict[str, Any] = {
            "length": len(display),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "preview": display[: self.preview_chars],
            "truncated": len(display) > self.preview_chars,
        }
        if self.include_full_text:
            summary["text"] = display
        return summary

    def summarize_jsonable(self, value: Any) -> dict[str, Any]:
        redacted = self.redact(value)
        try:
            serialized = json.dumps(redacted, ensure_ascii=False, sort_keys=True, default=str)
        except TypeError:
            serialized = json.dumps(str(redacted), ensure_ascii=False)

        summary = self.summarize_text(serialized)
        summary["json_type"] = type(value).__name__
        return summary

    def _envelope(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
    ) -> dict[str, Any]:
        self._sequence += 1
        envelope: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "sequence": self._sequence,
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "monotonic_ms": round((time.monotonic() - self._started_at) * 1000, 3),
            "event_type": event_type,
            "payload": payload,
        }
        if tool_call_id is not None:
            envelope["tool_call_id"] = tool_call_id
        if tool_name is not None:
            envelope["tool_name"] = tool_name
        return envelope

    def _write_sync(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, separators=(",", ":"), default=str)
            handle.write("\n")

    def _is_sensitive_key(self, key: str) -> bool:
        key_lower = key.lower()
        return any(part in key_lower for part in self.redact_key_parts)
