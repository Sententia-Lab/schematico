"""Smoke test for schematico.run_discovery against a real LLM.

Run with:
    uv run python cookbook/run_discovery.py

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
    district: str = Field(description="state and district, e.g. 'CA-12'")
    election_date: str = Field(description="election date in YYYY-MM-DD format")
    candidates: str = Field(
        description="a string-list of candidates running in the election"
    )


def main() -> None:
    model_list = [
        schematico.SchematicoModel(model="gateway/anthropic:claude-sonnet-4-6"),
        schematico.SchematicoModel(
            model="ollama:llama3.2", base_url="http://localhost:11434/v1"
        ),
    ]

    model = schematico.get_llm_model(model_list)

    records = schematico.run_discovery(
        schema=User,
        samples=60,
        instructions="Find me all congressional elections occurring in the 2026 midterms",
        model=model,
    )
    print(f"got {len(records)} records:")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
