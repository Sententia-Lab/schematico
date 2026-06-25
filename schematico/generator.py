from __future__ import annotations

from typing import Callable

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput, UsageLimits
from pydantic_ai.models import Model

from schematico.helpers import _hash_record, _build_prompt
from schematico.logging import get_logger
from schematico.models import build_batch_model
from schematico.schemas.helper_schemas import CallType
from schematico.providers import DEFAULT_MODEL
from schematico.prompts import GENERATOR_SYSTEM_PROMPT

logger = get_logger("core.generator")


def build_agent(
    schema: type[BaseModel],
    model: str | Model | None = None,
) -> Agent:
    resolved: str | Model = model if model is not None else DEFAULT_MODEL
    logger.debug("Building agent with model %r", resolved)
    batch_model = build_batch_model(schema, CallType.GENERATOR)

    agent = Agent(
        model=resolved,
        output_type=ToolOutput(batch_model),
        retries={"output": 5},
        system_prompt=GENERATOR_SYSTEM_PROMPT,
    )
    return agent


def run_generation(
    schema: type[BaseModel],
    samples: int,
    instructions: str,
    model: str | Model | None = None,
    logfire_token: str | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
    usage_limits: UsageLimits | None = UsageLimits(
        request_limit=5,
        tool_calls_limit=None,
        input_tokens_limit=None,
        output_tokens_limit=None,
        total_tokens_limit=100000,
        count_tokens_before_request=False,
    ),
) -> list[dict]:
    """
    Run a generation run to find structured data matching the provided schema.

    Args:
        schema: The Pydantic model representing the schema of the records to generate.
        samples: The number of records to generate.
        instructions: Instructions for the generation run.
        model: The model to use for the generation run. If None, the default model will be used.
        logfire_token: Optional token for Logfire logging. If None, logging to Logfire will be disabled.
        progress_cb: Optional callback function to report progress. It should accept three arguments: the number of unique records found, the total number of records requested, and a status string ("found" or "duplicate").
        usage_limits: Limits for the number of tokens and requests to use during the generation run.
            defaults to 5 requests and a total token limit of 100,000.

    Returns:
        A list of unique records generated, each represented as a dictionary.
    """
    if logfire_token:
        logfire.configure(token=logfire_token, send_to_logfire=True)
    else:
        logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()

    logger.info("Starting generation run (%d records requested)", samples)
    agent = build_agent(schema, model=model)
    result = agent.run_sync(
        _build_prompt(schema, samples, instructions),
        usage_limits=usage_limits,
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
