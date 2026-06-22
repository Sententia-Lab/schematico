from __future__ import annotations

import json

from pydantic_ai import Agent

from schematico.helpers import _generate_value
from schematico.logging import get_logger
from schematico.schema import Schema

logger = get_logger("core.tools")


def sample_record(schema: Schema) -> str:
    """Generate one example record using Faker as a reference baseline.

    Use this to see realistic example values for each field before
    producing your own records. You are not required to copy these
    values verbatim.
    """
    record = {f.name: _generate_value(f) for f in schema.fields}
    logger.debug("sample_record tool called, returning %s", record)
    return json.dumps(record, default=str)
