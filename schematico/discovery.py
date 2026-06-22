from __future__ import annotations

from typing import Callable
import os

import logfire
from pydantic_ai import Agent

from schematico.models import build_batch_model, build_record_model
from schematico.helpers import _hash_record
from schematico.logging import get_logger
from schematico.schema import Schema

logger = get_logger("core.discovery")

DEFAULT_MODEL = "gateway/anthropic:claude-sonnet-4-6"


def _resolve_model(model: str | None) -> str:
    return model or os.environ.get("PAI_MODEL") or DEFAULT_MODEL


def _build_prompt(schema: Schema) -> str:
    field_lines = []
    for f in schema.fields:
        line = f"- {f.name}: {f.type}"
        if f.values:
            line += f" (must be exactly one of: {f.values})"
        if f.min is not None or f.max is not None:
            line += f" (range: {f.min} to {f.max})"
        field_lines.append(line)

    prompt = (
        f"You are a data discovery agent for the '{schema.table}' table.\n"
        f"Find exactly {schema.rows} unique records with "
        "these fields:\n" + "\n".join(field_lines) + "\n\nRules:\n"
        "- Every record must be unique across all fields.\n"
        "- Enum fields must use only the declared values.\n"
        "- Numeric fields must respect any declared min/max range.\n"
        "- Use the sample_record tool if you want a realistic baseline "
        "example.\n"
        "- Return exactly the requested number of records."
    )
    if schema.instructions:
        prompt += f"\n\nAdditional instructions:\n{schema.instructions}"
    return prompt


def build_agent(schema: Schema, model: str | None = None) -> Agent:
    resolved = _resolve_model(model)
    logger.debug("Building agent for table '%s' with model %s", schema.table, resolved)
    record_model = build_record_model(schema)
    batch_model = build_batch_model(record_model)

    agent = Agent(
        model=resolved,
        output_type=batch_model,
        system_prompt=_build_prompt(schema),
    )
    return agent


def run_generation(
    schema: Schema,
    progress_cb: Callable[[int, int, str], None] | None = None,
    model: str | None = None,
    logfire_token: str | None = None,
) -> list[dict]:
    if logfire_token:
        logfire.configure(token=logfire_token, send_to_logfire=True)
    else:
        logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()

    logger.info(
        "Starting generation run for table '%s' (%d rows requested)",
        schema.table,
        schema.rows,
    )
    agent = build_agent(schema, model=model)
    result = agent.run_sync(
        f"Generate exactly {schema.rows} unique records "
        f"for the '{schema.table}' table."
    )
    logger.debug("Agent returned %d raw records", len(result.output.records))

    seen: dict[str, dict] = {}
    duplicates = 0
    for record in result.output.records:
        record_dict = record.model_dump()
        h = _hash_record(record_dict)

        if h in seen:
            duplicates += 1
            if progress_cb:
                progress_cb(len(seen), schema.rows, "duplicate")
            continue

        seen[h] = record_dict
        if progress_cb:
            progress_cb(len(seen), schema.rows, "found")

    logger.info(
        "Generation run complete: %d unique records (%d duplicates discarded)",
        len(seen),
        duplicates,
    )
    return list(seen.values())
