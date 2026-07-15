import json
import os

from aitrack.models.pricing import PricingConfig

_DEFAULT_PRICING = {
    "models": [
        {
            "provider": "opencode",
            "model_id": "big-pickle",
            "input_price_per_1k": 0.0,
            "output_price_per_1k": 0.0,
            "cache_read_price_per_1k": 0.0,
            "cache_write_price_per_1k": 0.0,
        },
        {
            "provider": "opencode",
            "model_id": "nemotron-3-ultra-free",
            "input_price_per_1k": 0.0,
            "output_price_per_1k": 0.0,
            "cache_read_price_per_1k": 0.0,
            "cache_write_price_per_1k": 0.0,
        },
        {
            "provider": "openai",
            "model_id": "gpt-5",
            "input_price_per_1k": 0.015,
            "output_price_per_1k": 0.060,
            "cache_read_price_per_1k": 0.0075,
            "cache_write_price_per_1k": 0.015,
        },
        {
            "provider": "anthropic",
            "model_id": "claude-sonnet-4",
            "input_price_per_1k": 0.003,
            "output_price_per_1k": 0.015,
            "cache_read_price_per_1k": 0.0003,
            "cache_write_price_per_1k": 0.00375,
        },
        {
            "provider": "anthropic",
            "model_id": "claude-opus-4",
            "input_price_per_1k": 0.015,
            "output_price_per_1k": 0.075,
            "cache_read_price_per_1k": 0.0015,
            "cache_write_price_per_1k": 0.01875,
        },
        {
            "provider": "anthropic",
            "model_id": "claude-haiku-4.5",
            "input_price_per_1k": 0.001,
            "output_price_per_1k": 0.005,
            "cache_read_price_per_1k": 0.0001,
            "cache_write_price_per_1k": 0.00125,
        },
        {
            "provider": "google",
            "model_id": "gemini-2.5-pro",
            "input_price_per_1k": 0.00125,
            "output_price_per_1k": 0.010,
            "cache_read_price_per_1k": 0.0000625,
            "cache_write_price_per_1k": 0.0,
        },
        {
            "provider": "openrouter",
            "model_id": "*",
            "input_price_per_1k": 0.0,
            "output_price_per_1k": 0.0,
            "cache_read_price_per_1k": 0.0,
            "cache_write_price_per_1k": 0.0,
        },
        {
            "provider": "kiro",
            "model_id": "auto",
            "input_price_per_1k": 0.0,
            "output_price_per_1k": 0.0,
            "cache_read_price_per_1k": 0.0,
            "cache_write_price_per_1k": 0.0,
        },
        {
            "provider": "kiro",
            "model_id": "claude-haiku-4.5",
            "input_price_per_1k": 0.001,
            "output_price_per_1k": 0.005,
            "cache_read_price_per_1k": 0.0001,
            "cache_write_price_per_1k": 0.00125,
        },
        {
            "provider": "kiro",
            "model_id": "claude-opus-4.8",
            "input_price_per_1k": 0.015,
            "output_price_per_1k": 0.075,
            "cache_read_price_per_1k": 0.0015,
            "cache_write_price_per_1k": 0.01875,
        },
        {
            "provider": "kiro",
            "model_id": "glm-5",
            "input_price_per_1k": 0.002,
            "output_price_per_1k": 0.008,
            "cache_read_price_per_1k": 0.0,
            "cache_write_price_per_1k": 0.0,
        },
    ]
}

_pricing_cache: PricingConfig | None = None


def _get_config_path() -> str:
    xdg = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(xdg, "aitrack", "pricing.json")


def get_pricing() -> PricingConfig:
    global _pricing_cache
    if _pricing_cache is not None:
        return _pricing_cache
    path = _get_config_path()
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        _pricing_cache = PricingConfig(**data)
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(_DEFAULT_PRICING, f, indent=2)
        _pricing_cache = PricingConfig(**_DEFAULT_PRICING)
    return _pricing_cache


def clear_pricing_cache() -> None:
    """Clear the pricing cache (useful for testing)."""
    global _pricing_cache
    _pricing_cache = None


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    pricing = get_pricing()
    entry = pricing.find(provider, model)
    if entry is None:
        entry = pricing.find(provider, "*")
    if entry is None:
        return 0.0
    cost = (
        (input_tokens / 1000) * entry.input_price_per_1k
        + (output_tokens / 1000) * entry.output_price_per_1k
        + (cache_read_tokens / 1000) * entry.cache_read_price_per_1k
        + (cache_write_tokens / 1000) * entry.cache_write_price_per_1k
    )
    return round(cost, 6)
