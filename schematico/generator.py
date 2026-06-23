from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Callable

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent

from schematico.logging import get_logger
from schematico.models import build_batch_model

logger = get_logger("core.generator")

DEFAULT_MODEL = "gateway/anthropic:claude-sonnet-4-6"


def _resolve_model(model: str | None) -> str:
    return model or os.environ.get("PAI_MODEL") or DEFAULT_MODEL


def _table_name(schema: type[BaseModel]) -> str:
    name = schema.__name__
    if name.endswith("Record"):
        name = name[: -len("Record")]
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _hash_record(record: dict) -> str:
    serialized = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


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
    table = _table_name(schema)
    field_lines = _describe_fields(schema)
    prompt = (
        f"You are a data generation agent for the '{table}' table.\n"
        f"Generate exactly {samples} realistic, unique records with "
        "these fields:\n" + "\n".join(field_lines) + "\n\nRules:\n"
        "- Every record must be unique across all fields.\n"
        "- Enum fields must use only the declared values.\n"
        "- Numeric fields must respect any declared min/max range.\n"
        "- Return exactly the requested number of records."
    )
    if instructions:
        prompt += f"\n\nAdditional instructions:\n{instructions}"
    return prompt


def build_agent(
    schema: type[BaseModel],
    samples: int,
    instructions: str = "",
    model: str | None = None,
) -> Agent:
    resolved = _resolve_model(model)
    table = _table_name(schema)
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
    model: str | None = None,
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
