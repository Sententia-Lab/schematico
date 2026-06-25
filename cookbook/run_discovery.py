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
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import schematico
import os

load_dotenv()


class Election(BaseModel):
    district: str = Field(description="state and district, e.g. 'CA-12'")
    election_date: str = Field(description="election date in YYYY-MM-DD format")
    candidates: str = Field(
        description="a string-list of candidates running in the election"
    )


class Weather(BaseModel):
    year: int = Field(description="The year of the weather data")
    location: str = Field(description="NYC")
    month: str = Field(
        description="The month of the year (e.g. 'January', 'February', etc.)"
    )
    average_temperature: float = Field(
        description="Average temperature in degrees Fahrenheit for the month"
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
        schema=Weather,
        samples=12,
        instructions="Find me the average weather per month in NYC in degrees Fahrenheit for the 12 months of 2025",
        model=model,
        logfire_token=os.environ.get("LOGFIRE_TOKEN"),
    )
    print(f"got {len(records)} records:")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
