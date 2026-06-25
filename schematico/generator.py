from __future__ import annotations

from typing import Callable

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput
from pydantic_ai.models import Model

from schematico.helpers import _table_name, _hash_record, _describe_fields
from schematico.logging import get_logger
from schematico.models import build_batch_model
from schematico.providers import DEFAULT_MODEL

logger = get_logger("core.generator")


def _build_prompt(schema: type[BaseModel], samples: int, instructions: str) -> str:
    table = _table_name(schema)
    field_lines = _describe_fields(schema)
    prompt = (
        f"You are a data generation agent for the '{table}' table.\n"
        f"Generate exactly {samples} realistic, unique records with "
        "these fields:\n" + "\n".join(field_lines) + "\n\nRules:\n"
        "- Every record must be unique across all fields.\n"
        "- Enum fields must use only the declared values.\n"
        "- Numeric fields must respect any declared min/max range.\n"
        "- Return exactly the requested number of records.\n"
        "- Your FINAL answer must be returned via the structured output, "
        "never as a plain-text message."
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
    table = _table_name(schema)
    logger.debug("Building agent for '%s' with model %r", table, resolved)
    batch_model = build_batch_model(schema)

    agent = Agent(
        model=resolved,
        output_type=ToolOutput(batch_model),
        retries={"output": 5},
        system_prompt=_build_prompt(schema, samples, instructions),
    )
    return agent


def run_generation(
    schema: type[BaseModel],
    samples: int,
    instructions: str = "",
    model: str | Model | None = None,
    logfire_token: str | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> list[dict]:
    if logfire_token:
        logfire.configure(token=logfire_token, send_to_logfire=True)
    else:
        logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()

    table = _table_name(schema)
    logger.info(
        "Starting generation run for '%s' (%d records requested)", table, samples
    )
    agent = build_agent(schema, samples, instructions, model=model)
    result = agent.run_sync(
        f"Generate exactly {samples} unique records for the '{table}' table."
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
                progress_cb(len(seen), samples, "duplicate")
            continue
        seen[h] = record_dict
        if progress_cb:
            progress_cb(len(seen), samples, "found")

    logger.info(
        "Generation run complete: %d unique records (%d duplicates discarded)",
        len(seen),
        duplicates,
    )
    return list(seen.values())
