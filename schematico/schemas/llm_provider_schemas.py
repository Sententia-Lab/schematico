from pydantic import BaseModel


class SchematicoModel(BaseModel):
    """One entry in a fallback chain.

    `model` is a pydantic-ai model string ("anthropic:claude-sonnet-4-6",
    "gateway/openai:gpt-4o", "ollama:llama3.1", …). `api_key` and `base_url` are
    optional; when left as None, pydantic-ai reads the provider's env var.
    """

    model: str
    api_key: str | None = None
    base_url: str | None = None
