from __future__ import annotations

import os

import httpx

from schematico.logging import get_logger

logger = get_logger("core.gateway")

GATEWAY_BASES = {
    "us": "https://gateway-us.pydantic.dev",
    "eu": "https://gateway-eu.pydantic.dev",
}

DEFAULT_REGION = "us"
PROVIDERS = ("openai", "anthropic")
REQUEST_TIMEOUT = 10.0

ANTHROPIC_FALLBACK_MODELS = (
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
)


def gateway_base(region: str | None = None) -> str:
    r = region or os.environ.get("SCHEMATICO_GATEWAY_REGION", DEFAULT_REGION)
    if r not in GATEWAY_BASES:
        raise ValueError(f"Unknown gateway region '{r}'. Valid: {list(GATEWAY_BASES)}")
    return GATEWAY_BASES[r]


def _list_provider_models(client: httpx.Client, base: str, provider: str) -> list[str]:
    url = f"{base}/proxy/{provider}/v1/models"
    resp = client.get(url)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data", [])
    return [item["id"] for item in data if "id" in item]


def list_models(api_key: str, region: str | None = None) -> list[str]:
    base = gateway_base(region)
    headers = {"Authorization": f"Bearer {api_key}"}
    out: list[str] = []

    with httpx.Client(headers=headers, timeout=REQUEST_TIMEOUT) as client:
        for provider in PROVIDERS:
            try:
                ids = _list_provider_models(client, base, provider)
                out.extend(f"gateway/{provider}:{mid}" for mid in ids)
            except Exception as e:  # noqa: BLE001
                if provider == "anthropic":
                    logger.warning(
                        "Gateway list-models failed for %s (%s); using fallback list",
                        provider,
                        e,
                    )
                    out.extend(
                        f"gateway/anthropic:{m}" for m in ANTHROPIC_FALLBACK_MODELS
                    )
                else:
                    logger.warning("Gateway list-models failed for %s: %s", provider, e)

    return sorted(set(out))
