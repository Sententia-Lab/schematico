import logfire
from pydantic import BaseModel
from pydantic_ai.models import Model
from pydantic_ai.agent import Agent
from pydantic_ai import ToolOutput, UsageLimits
from typing import Callable

from schematico.helpers import _hash_record, _build_prompt
from schematico.logging import get_logger
from schematico.models import build_batch_model
from schematico.schemas.helper_schemas import CallType
from schematico.providers import DEFAULT_MODEL
from schematico.tools.tavily_tools import web_search_toolset
from schematico.tools.statistical_tools import statistic_toolset
from schematico.prompts import DISCOVERY_SYSTEM_PROMPT

logger = get_logger("core.discovery")


def build_agent(
    schema: type[BaseModel],
    model: str | Model | None = None,
) -> Agent:
    resolved: str | Model = model if model is not None else DEFAULT_MODEL
    logger.debug("Building agent with model %r", resolved)
    batch_model = build_batch_model(schema, caller=CallType.DISCOVERY)

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
    Run a discovery run to find structured data matching the provided schema.

    Args:
        schema: The Pydantic model representing the schema of the records to discover.
        samples: The number of records to discover.
        instructions: Instructions for the discovery run.
        model: The model to use for the discovery run. If None, the default model will be used.
        logfire_token: Optional token for Logfire logging. If None, logging to Logfire will be disabled.
        progress_cb: Optional callback function to report progress. It should accept three arguments: the number of unique records found, the total number of records requested, and a status string ("found" or "duplicate").
        usage_limits: Limits for the number of tokens and requests to use during the discovery run.
            defaults to 5 requests and a total token limit of 100,000.

    Returns:
        A list of unique records discovered, each represented as a dictionary.
    """
    if logfire_token:
        logfire.configure(token=logfire_token, send_to_logfire=True, scrubbing=False)
    else:
        logfire.configure(send_to_logfire=False, scrubbing=False)
    logfire.instrument_pydantic_ai()

    logger.info("Starting discovery run (%d records requested)", samples)
    agent = build_agent(schema, model)
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
        "Discovery run complete: %d unique records (%d duplicates discarded)",
        len(seen),
        duplicates,
    )
    return list(seen.values())
