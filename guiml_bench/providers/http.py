from __future__ import annotations

import os
import time
from typing import Any

import httpx

from .base import Message, Usage


class OpenAICompat:
    """OpenAI-compatible chat completions (OpenAI, Mistral, many gateways)."""

    def __init__(self, name: str, model: str, base_url: str, api_key_env: str, *, input_cost=0.0, output_cost=0.0):
        self.name = name
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.input_cost = input_cost
        self.output_cost = output_cost

    def complete(self, messages: list[Message], *, tools=None, json_mode=False, temperature=0.2, max_tokens=4096):
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"{self.api_key_env} is not set")
        body: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
        t0 = time.time()
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=body,
            timeout=120.0,
        )
        r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]["message"]
        text = choice.get("content") or ""
        calls = []
        for tc in choice.get("tool_calls") or []:
            fn = tc.get("function") or {}
            calls.append({"name": fn.get("name"), "arguments": fn.get("arguments")})
        usage_raw = data.get("usage") or {}
        inn = int(usage_raw.get("prompt_tokens") or 0)
        out = int(usage_raw.get("completion_tokens") or 0)
        cost = inn * self.input_cost + out * self.output_cost
        return text, Usage(inn, out, cost, time.time() - t0), calls


class AnthropicCompat:
    def __init__(self, name: str, model: str, api_key_env: str = "ANTHROPIC_API_KEY", *, input_cost=0.0, output_cost=0.0):
        self.name = name
        self.model = model
        self.api_key_env = api_key_env
        self.input_cost = input_cost
        self.output_cost = output_cost

    def complete(self, messages: list[Message], *, tools=None, json_mode=False, temperature=0.2, max_tokens=4096):
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"{self.api_key_env} is not set")
        sys_msgs = [m.content for m in messages if m.role == "system"]
        user_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": user_msgs or [{"role": "user", "content": ""}],
        }
        if sys_msgs:
            body["system"] = "\n\n".join(sys_msgs)
        t0 = time.time()
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json=body,
            timeout=120.0,
        )
        r.raise_for_status()
        data = r.json()
        text = "".join(p.get("text", "") for p in data.get("content", []) if p.get("type") == "text")
        usage_raw = data.get("usage") or {}
        inn = int(usage_raw.get("input_tokens") or 0)
        out = int(usage_raw.get("output_tokens") or 0)
        return text, Usage(inn, out, inn * self.input_cost + out * self.output_cost, time.time() - t0), []


class HFInference:
    def __init__(self, name: str, model: str, api_key_env: str = "HF_TOKEN"):
        self.name = name
        self.model = model
        self.api_key_env = api_key_env

    def complete(self, messages: list[Message], *, tools=None, json_mode=False, temperature=0.2, max_tokens=4096):
        key = os.environ.get(self.api_key_env, "") or os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")
        if not key:
            raise RuntimeError("HF_TOKEN is not set")
        t0 = time.time()
        r = httpx.post(
            f"https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": self.model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
            },
            timeout=180.0,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        usage_raw = data.get("usage") or {}
        return (
            text,
            Usage(int(usage_raw.get("prompt_tokens") or 0), int(usage_raw.get("completion_tokens") or 0), None, time.time() - t0),
            [],
        )
