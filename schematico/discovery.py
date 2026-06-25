import logfire
from pydantic import BaseModel
from pydantic_ai.models import Model
from pydantic_ai.agent import Agent
from pydantic_ai import ToolOutput, UsageLimits
from typing import Callable

from schematico.helpers import _hash_record, _build_prompt
from schematico.logging import get_logger
from schematico.models import build_batch_model
from schematico.providers import DEFAULT_MODEL
from schematico.tools.tavily_tools import web_search_toolset
from schematico.tools.statistic_tools import statistic_toolset
from schematico.prompts import DISCOVERY_SYSTEM_PROMPT

logger = get_logger("core.discovery")


def build_agent(
    schema: type[BaseModel],
    model: str | Model | None = None,
) -> Agent:
    resolved: str | Model = model if model is not None else DEFAULT_MODEL
    logger.debug("Building agent with model %r", resolved)
    batch_model = build_batch_model(schema, caller="discovery")

    agent = Agent(
        model=resolved,
        output_type=ToolOutput(batch_model),
        retries={"output": 2},
        system_prompt=DISCOVERY_SYSTEM_PROMPT,
        toolsets=[web_search_toolset, statistic_toolset],
    )
    return agent


def run_discovery(
    schema: type[BaseModel],
    samples: int,
    instructions: str = "",
    model: str | Model | None = None,
    logfire_token: str | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> list[dict]:
    if logfire_token:
        logfire.configure(token=logfire_token, send_to_logfire=True, scrubbing=False)
    else:
        logfire.configure(send_to_logfire=False, scrubbing=False)
    logfire.instrument_pydantic_ai()

    logger.info("Starting discovery run (%d records requested)", samples)
    agent = build_agent(schema, model)
    result = agent.run_sync(
        _build_prompt(schema, samples, instructions),
        usage_limits=UsageLimits(request_limit=8, total_tokens_limit=100_000),
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
