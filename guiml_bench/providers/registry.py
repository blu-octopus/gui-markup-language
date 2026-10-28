from __future__ import annotations

from .http import AnthropicCompat, HFInference, OpenAICompat
from .mock import MockProvider

# model id → factory. Cost per token is a placeholder; override via env if needed.
PROVIDERS = {
    "mock": lambda model="mock-v1": MockProvider(),
    "mistral": lambda model="mistral-large-latest": OpenAICompat(
        "mistral", model, "https://api.mistral.ai/v1", "MISTRAL_API_KEY", input_cost=2e-6, output_cost=6e-6
    ),
    "openai": lambda model="gpt-4o": OpenAICompat(
        "openai", model, "https://api.openai.com/v1", "OPENAI_API_KEY", input_cost=2.5e-6, output_cost=1e-5
    ),
    "anthropic": lambda model="claude-sonnet-4-20250514": AnthropicCompat(
        "anthropic", model, input_cost=3e-6, output_cost=1.5e-5
    ),
    "hf": lambda model="Qwen/Qwen2.5-Coder-32B-Instruct": HFInference("hf", model),
}


def get_provider(spec: str):
    """spec is 'mock' or 'mistral:mistral-large-latest' etc."""
    if ":" in spec:
        name, model = spec.split(":", 1)
    else:
        name, model = spec, None
    if name not in PROVIDERS:
        raise KeyError(f"unknown provider {name}; known: {sorted(PROVIDERS)}")
    fn = PROVIDERS[name]
    return fn() if model is None and name == "mock" else fn(model) if model else fn()
