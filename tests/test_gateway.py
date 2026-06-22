from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from schematico import gateway


def _patch_client(monkeypatch: pytest.MonkeyPatch, handler):
    def make_client(**kw):
        return httpx.Client(transport=httpx.MockTransport(handler), **kw)

    fake = SimpleNamespace(Client=make_client)
    monkeypatch.setattr(gateway, "httpx", fake)


def test_list_models_merges_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        assert request.headers["authorization"] == "Bearer test-key"
        if "openai" in str(request.url):
            return httpx.Response(
                200, json={"data": [{"id": "gpt-4.1"}, {"id": "gpt-4o"}]}
            )
        if "anthropic" in str(request.url):
            return httpx.Response(200, json={"data": [{"id": "claude-sonnet-4-6"}]})
        return httpx.Response(404)

    _patch_client(monkeypatch, handler)

    result = gateway.list_models("test-key")
    assert "gateway/openai:gpt-4.1" in result
    assert "gateway/openai:gpt-4o" in result
    assert "gateway/anthropic:claude-sonnet-4-6" in result
    assert len(calls) == 2


def test_list_models_falls_back_for_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "openai" in str(request.url):
            return httpx.Response(200, json={"data": [{"id": "gpt-4.1"}]})
        return httpx.Response(500, text="oops")

    _patch_client(monkeypatch, handler)

    result = gateway.list_models("k")
    assert "gateway/openai:gpt-4.1" in result
    for fallback in gateway.ANTHROPIC_FALLBACK_MODELS:
        assert f"gateway/anthropic:{fallback}" in result


def test_list_models_openai_failure_is_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "openai" in str(request.url):
            return httpx.Response(500)
        return httpx.Response(200, json={"data": [{"id": "claude-sonnet-4-6"}]})

    _patch_client(monkeypatch, handler)

    result = gateway.list_models("k")
    assert all(not m.startswith("gateway/openai:") for m in result)
    assert "gateway/anthropic:claude-sonnet-4-6" in result


def test_gateway_base_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCHEMATICO_GATEWAY_REGION", raising=False)
    assert gateway.gateway_base() == "https://gateway-us.pydantic.dev"


def test_gateway_base_unknown_region() -> None:
    with pytest.raises(ValueError):
        gateway.gateway_base("mars")
