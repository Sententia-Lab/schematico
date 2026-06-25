"""Smoke test for schematico.run_generation against a real LLM.

Run with:
    uv run python cookbook/run_generation.py

Pick a provider by setting one of:
    PYDANTIC_AI_GATEWAY_API_KEY   (default, uses gateway/anthropic:claude-sonnet-4-6)
    ANTHROPIC_API_KEY             (then pass model="anthropic:claude-sonnet-4-6")
    OPENAI_API_KEY                (then pass model="openai:gpt-4o-mini")
    (none, for ollama:llama3.1 against a local Ollama)
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

import schematico


class User(BaseModel):
    full_name: str = Field(description="realistic full name")
    email: str = Field(description="unique work email")
    role: str = Field(description="one of: admin, editor, viewer")
    country: str = Field(description="ISO 3166-1 alpha-2 country code")


def main() -> None:
    model_list = [
        schematico.SchematicoModel(model="gateway/anthropic:claude-sonnet-4-6"),
        schematico.SchematicoModel(
            model="ollama:llama3.2", base_url="http://localhost:11434/v1"
        ),
    ]

    model = schematico.get_llm_model(model_list)

    records = schematico.run_generation(
        User,
        samples=5,
        instructions="EU-based users only. Emails must match the full_name.",
        model=model,
    )
    print(f"got {len(records)} records:")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
