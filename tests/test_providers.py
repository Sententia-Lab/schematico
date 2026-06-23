from __future__ import annotations

from schematico import providers


def test_env_key_for_known_providers() -> None:
    assert providers.env_key_for("anthropic:claude-x") == "ANTHROPIC_API_KEY"
    assert providers.env_key_for("openai:gpt-4o") == "OPENAI_API_KEY"
    assert providers.env_key_for("groq:llama-3.3-70b") == "GROQ_API_KEY"
    assert providers.env_key_for("mistral:large-latest") == "MISTRAL_API_KEY"
    assert providers.env_key_for("openrouter:foo/bar") == "OPENROUTER_API_KEY"
    assert (
        providers.env_key_for("gateway/anthropic:claude-x")
        == "PYDANTIC_AI_GATEWAY_API_KEY"
    )


def test_env_key_for_keyless_providers() -> None:
    assert providers.env_key_for("ollama:llama3.1") is None
    assert providers.env_key_for("bedrock:anthropic.claude-3") is None
    assert providers.env_key_for("google-vertex:gemini-1.5") is None


def test_env_key_for_unknown_provider() -> None:
    assert providers.env_key_for("madeup:model-id") is None


def test_env_key_for_unstructured() -> None:
    assert providers.env_key_for("just-a-name") is None


def test_default_model_present() -> None:
    assert providers.DEFAULT_MODEL.startswith("gateway/")
