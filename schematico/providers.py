from __future__ import annotations

DEFAULT_MODEL = "gateway/anthropic:claude-sonnet-4-6"

# Env var each pydantic-ai provider expects for its API key. Sourced from
# https://pydantic.dev/docs/ai/models/overview/. `None` means the provider
# doesn't need a key (local) or uses ambient credentials (e.g. AWS for bedrock).
PROVIDER_ENV_KEYS: dict[str, str | None] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "google-gla": "GEMINI_API_KEY",
    "google-vertex": None,
    "xai": "XAI_API_KEY",
    "bedrock": None,
    "cerebras": "CEREBRAS_API_KEY",
    "cohere": "COHERE_API_KEY",
    "groq": "GROQ_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "ollama": None,
    "openrouter": "OPENROUTER_API_KEY",
    "gateway": "PYDANTIC_AI_GATEWAY_API_KEY",
}


def env_key_for(model: str) -> str | None:
    """Return the env var required for a pydantic-ai model string, or None.

    Returns None for unknown providers, local providers (ollama), and providers
    that use ambient credentials (bedrock, google-vertex).
    """
    if ":" not in model:
        return None
    prefix = model.split(":", 1)[0]
    if prefix.startswith("gateway/"):
        prefix = "gateway"
    return PROVIDER_ENV_KEYS.get(prefix)
