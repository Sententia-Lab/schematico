from __future__ import annotations

from typing import Callable

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai.models import Model, infer_model
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.providers import Provider, infer_provider, infer_provider_class
from pydantic_ai.providers.gateway import gateway_provider

DEFAULT_MODEL = "gateway/anthropic:claude-sonnet-4-6"
load_dotenv()


class SchematicoModel(BaseModel):
    """One entry in a fallback chain.

    `model` is a pydantic-ai model string ("anthropic:claude-sonnet-4-6",
    "gateway/openai:gpt-4o", "ollama:llama3.1", …). `api_key` and `base_url` are
    optional; when left as None, pydantic-ai reads the provider's env var.
    """

    model: str
    api_key: str | None = None
    base_url: str | None = None


def _provider_factory(spec: SchematicoModel) -> Callable[[str], Provider]:
    def factory(provider_name: str) -> Provider:
        if spec.api_key is None and spec.base_url is None:
            return infer_provider(provider_name)
        kwargs: dict[str, str] = {}
        if spec.api_key is not None:
            kwargs["api_key"] = spec.api_key
        if spec.base_url is not None:
            kwargs["base_url"] = spec.base_url
        if provider_name.startswith("gateway/"):
            upstream = provider_name.removeprefix("gateway/")
            return gateway_provider(upstream, **kwargs)
        cls = infer_provider_class(provider_name)
        return cls(**kwargs)

    return factory


def get_llm_model(
    models: str | SchematicoModel | list[SchematicoModel],
) -> Model:
    """Resolve one or more model specs into a single pydantic-ai Model.

    - `str`                  → `infer_model(str)` (env-var creds)
    - `SchematicoModel`      → single Model with per-spec creds
    - `list[SchematicoModel]`→ `FallbackModel(*resolved)` for failover (or the
      single resolved Model if the list has one entry).

    Example usage:
    1. Single model with env-var creds:
    ```
    model = schematico.get_llm_model(
        schematico.SchematicoModel(
            model="anthropic:claude-sonnet-4-6",
        )
    )
    ```

    2. Single model with env-var creds:
    ```
    model = schematico.get_llm_model(
        schematico.SchematicoModel(
            model="anthropic:claude-sonnet-4-6",
            api_key="sk-ant-...",
        )
    )
    ```

    3. Or a failover chain (tries each in order):
    ```
    model = schematico.get_llm_model([
        schematico.SchematicoModel(model="anthropic:claude-sonnet-4-6"),
        schematico.SchematicoModel(model="openai:gpt-4o-mini"),
    ])
    ```
    """
    if isinstance(models, str):
        return infer_model(models)
    if isinstance(models, SchematicoModel):
        return infer_model(models.model, provider_factory=_provider_factory(models))
    if not models:
        raise ValueError("get_llm_model: empty model list")

    resolved = [
        infer_model(m.model, provider_factory=_provider_factory(m)) for m in models
    ]
    return resolved[0] if len(resolved) == 1 else FallbackModel(*resolved)
