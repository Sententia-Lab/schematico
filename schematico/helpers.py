import hashlib
import json

# import re
from typing import Any

from pydantic import BaseModel


def _hash_record(record: dict) -> str:
    serialized = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _describe_fields(schema: type[BaseModel]) -> str:
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
    return "\n".join(lines)


def _build_prompt(schema: type[BaseModel], samples: int, instructions: str) -> str:
    fields = _describe_fields(schema)
    prompt = f"""
    instructions: {instructions}
    records: {samples}
    schema:
    {fields}
    """
    return prompt.strip()
