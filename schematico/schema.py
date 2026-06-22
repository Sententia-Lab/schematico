from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from schematico.logging import get_logger

logger = get_logger("core.schema")

SUPPORTED_TYPES = frozenset(
    {
        "uuid",
        "full_name",
        "email",
        "enum",
        "country",
        "timestamp",
        "int",
        "integer",
        "string",
        "boolean",
        "float",
        "decimal",
    }
)

DEFAULT_ROW_COUNT = 25


@dataclass
class FieldSpec:
    name: str
    type: str
    values: list[str] = field(default_factory=list)
    min: int | float | None = None
    max: int | float | None = None


@dataclass
class Schema:
    table: str
    fields: list[FieldSpec]
    rows: int
    instructions: str = ""


def load_schema(path: str, count_override: int | None = None) -> Schema:
    logger.debug("Loading schema from '%s'", path)
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: '{path}'")

    with p.open(encoding="utf-8") as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in '{path}': {e}") from e

    return load_schema_from_dict(raw, count_override=count_override)


def load_schema_from_dict(raw: dict, count_override: int | None = None) -> Schema:
    if not isinstance(raw, dict):
        raise ValueError("Schema must be a mapping at the top level")

    table = raw.get("table")
    if not table or not isinstance(table, str):
        raise ValueError("Schema must have a non-empty string field 'table'")

    raw_fields = raw.get("fields")
    if not raw_fields or not isinstance(raw_fields, list):
        raise ValueError("Schema must have a non-empty list field 'fields'")

    fields: list[FieldSpec] = []
    for i, f_raw in enumerate(raw_fields):
        name = f_raw.get("name")
        if not name or not isinstance(name, str):
            raise ValueError(f"Field at index {i} must have a non-empty 'name'")

        ftype = f_raw.get("type", "")
        if not isinstance(ftype, str) or ftype.lower() not in SUPPORTED_TYPES:
            supported = ", ".join(sorted(SUPPORTED_TYPES))
            raise ValueError(
                f"Unknown field type '{ftype}' for field '{name}'. "
                f"Supported types: {supported}"
            )
        ftype = ftype.lower()

        values = f_raw.get("values", [])
        if ftype == "enum" and not values:
            raise ValueError(f"Enum field '{name}' must have a non-empty 'values' list")

        fields.append(
            FieldSpec(
                name=name,
                type=ftype,
                values=values,
                min=f_raw.get("min"),
                max=f_raw.get("max"),
            )
        )

    if count_override is not None:
        rows = count_override
    elif "rows" in raw and isinstance(raw["rows"], int):
        rows = raw["rows"]
    else:
        rows = DEFAULT_ROW_COUNT

    instructions = raw.get("instructions", "") or ""
    if not isinstance(instructions, str):
        raise ValueError("'instructions' must be a string if provided")

    logger.debug("Parsed schema '%s': %d fields, rows=%d", table, len(fields), rows)
    return Schema(
        table=table, fields=fields, rows=rows, instructions=instructions.strip()
    )
