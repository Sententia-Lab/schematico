from __future__ import annotations

import re
from typing import Any

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import Model

from schematico.helpers import de_duplicate_records
from schematico.logging import get_logger
from schematico.models import build_batch_model
from schematico.providers import DEFAULT_MODEL
from schematico.tools import sample_record

logger = get_logger("core.generator")


def _snake_case(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _describe_fields(schema: type[BaseModel]) -> list[str]:
    json_schema = schema.model_json_schema()
    properties: dict[str, dict[str, Any]] = json_schema.get("properties", {})
    lines: list[str] = []
    for name, prop in properties.items():
        ptype = prop.get("type") or prop.get("anyOf") or "any"
        line = f"- {name}: {ptype}"
        desc = prop.get("description")
        if desc:
            line += f" — {desc}"
        if "enum" in prop:
            line += f" (must be exactly one of: {prop['enum']})"
        lo, hi = prop.get("minimum"), prop.get("maximum")
        if lo is not None or hi is not None:
            line += f" (range: {lo} to {hi})"
        lines.append(line)
    return lines


def _build_prompt(schema: type[BaseModel], samples: int, instructions: str) -> str:
    table = _snake_case(schema.__name__)
    field_lines = _describe_fields(schema)
    prompt = (
        f"You are a data generation agent for the '{table}' table.\n"
        f"Generate exactly {samples} realistic, unique records with "
        "these fields:\n" + "\n".join(field_lines) + "\n\nRules:\n"
        "- Every record must be unique across all fields.\n"
        "- Enum fields must use only the declared values.\n"
        "- Numeric fields must respect any declared min/max range.\n"
        "- Use the sample_record tool if you want a realistic baseline "
        "example.\n"
        "- Return exactly the requested number of records."
    )
    if instructions:
        prompt += f"\n\nAdditional instructions:\n{instructions}"
    return prompt


def build_agent(
    schema: type[BaseModel],
    samples: int,
    instructions: str = "",
    model: str | Model | None = None,
) -> Agent:
    resolved: str | Model = model if model is not None else DEFAULT_MODEL
    table = _snake_case(schema.__name__)
    logger.debug("Building agent for '%s' with model %r", table, resolved)
    batch_model = build_batch_model(schema)

    agent = Agent(
        model=resolved,
        output_type=batch_model,
        system_prompt=_build_prompt(schema, samples, instructions),
    )
    return agent


def run_generation(
    schema: type[BaseModel],
    samples: int,
    instructions: str = "",
    model: str | Model | None = None,
    logfire_token: str | None = None,
) -> list[dict]:
    if logfire_token:
        logfire.configure(token=logfire_token, send_to_logfire=True)
    else:
        logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()

    table = _snake_case(schema.__name__)
    logger.info(
        "Starting generation run for '%s' (%d records requested)", table, samples
    )
    agent = build_agent(schema, samples, instructions, model=model)
    result = agent.run_sync(
        f"Generate exactly {samples} unique records for the '{table}' table."
    )
    logger.debug("Agent returned %d raw records", len(result.output.records))

    deduped = de_duplicate_records(result.output.records, logger)
    return deduped
