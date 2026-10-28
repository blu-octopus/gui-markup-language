from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    latency_s: float = 0.0


@dataclass
class Message:
    role: str
    content: str
    name: str | None = None


class Provider(Protocol):
    name: str
    model: str

    def complete(
        self,
        messages: list[Message],
        *,
        tools: list[dict[str, Any]] | None = None,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[str, Usage, list[dict[str, Any]]]:
        """Return (text, usage, tool_calls). tool_calls is empty if none."""
        ...
