from __future__ import annotations

import pytest
from pydantic_ai.models import Model
from pydantic_ai.models.fallback import FallbackModel

from schematico import providers
from schematico.providers import SchematicoModel, get_llm_model


def test_default_model_present() -> None:
    assert providers.DEFAULT_MODEL.startswith("gateway/")


def test_get_llm_model_string_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    m = get_llm_model("anthropic:claude-sonnet-4-5")
    assert isinstance(m, Model)


def test_get_llm_model_schematicomodel_injects_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    spec = SchematicoModel(model="anthropic:claude-sonnet-4-5", api_key="sk-explicit")
    m = get_llm_model(spec)
    assert isinstance(m, Model)
    # AnthropicProvider stores creds on its inner SDK client.
    assert m.client.api_key == "sk-explicit"


def test_get_llm_model_list_returns_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    specs = [
        SchematicoModel(model="anthropic:claude-sonnet-4-5", api_key="sk-a"),
        SchematicoModel(model="openai:gpt-4o-mini", api_key="sk-o"),
    ]
    m = get_llm_model(specs)
    assert isinstance(m, FallbackModel)
    assert len(m.models) == 2


def test_get_llm_model_singleton_list_unwraps() -> None:
    m = get_llm_model([SchematicoModel(model="anthropic:claude-x", api_key="sk")])
    assert isinstance(m, Model)
    assert not isinstance(m, FallbackModel)


def test_get_llm_model_empty_list_raises() -> None:
    with pytest.raises(ValueError):
        get_llm_model([])
