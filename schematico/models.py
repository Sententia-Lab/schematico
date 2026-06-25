from __future__ import annotations

import json
import keyword
from pathlib import Path
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, create_model

_PRIMITIVES: dict[str, type] = {
    "string": str,
    "int": int,
    "float": float,
    "bool": bool,
}

_ALLOWED_TOP_KEYS = {"table", "fields", "rows", "instructions"}
_ALLOWED_FIELD_KEYS = {"name", "type", "description", "values", "min", "max"}


def _validate_identifier(name: str) -> None:
    if not isinstance(name, str) or not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError(
            f"Field name '{name}' must be a valid Python identifier "
            "(and not a reserved keyword)"
        )


def _build_field(spec: dict[str, Any]) -> tuple[type, Any]:
    if not isinstance(spec, dict):
        raise ValueError(f"Field entry must be an object, got {type(spec).__name__}")

    unknown = set(spec) - _ALLOWED_FIELD_KEYS
    if unknown:
        raise ValueError(
            f"Field '{spec.get('name', '?')}': unknown keys {sorted(unknown)}. "
            f"Allowed: {sorted(_ALLOWED_FIELD_KEYS)}"
        )

    name = spec.get("name", "")
    _validate_identifier(name)

    ftype = spec.get("type")
    description = spec.get("description", "") or ""

    if ftype == "enum":
        values = spec.get("values") or []
        if not isinstance(values, list) or not values:
            raise ValueError(f"Field '{name}': enum requires a non-empty 'values' list")
        py_type = Literal[tuple(values)]  # type: ignore[valid-type]
        return py_type, Field(description=description)

    if ftype not in _PRIMITIVES:
        raise ValueError(
            f"Field '{name}': unknown type '{ftype}'. "
            f"Use one of: {sorted(_PRIMITIVES) + ['enum']}"
        )

    py_type = _PRIMITIVES[ftype]
    kwargs: dict[str, Any] = {"description": description}
    lo, hi = spec.get("min"), spec.get("max")
    if lo is not None and ftype not in ("int", "float"):
        raise ValueError(f"Field '{name}': 'min' only valid for int/float")
    if hi is not None and ftype not in ("int", "float"):
        raise ValueError(f"Field '{name}': 'max' only valid for int/float")
    if lo is not None:
        kwargs["ge"] = lo
    if hi is not None:
        kwargs["le"] = hi
    return py_type, Field(**kwargs)


def model_from_dict(raw: dict) -> tuple[type[BaseModel], int, str]:
    """Convert a JSON-schema dict into (RecordModel, rows, instructions)."""
    if not isinstance(raw, dict):
        raise ValueError("Schema must be a mapping at the top level")

    unknown = set(raw) - _ALLOWED_TOP_KEYS
    if unknown:
        raise ValueError(
            f"Unknown top-level keys {sorted(unknown)}. "
            f"Allowed: {sorted(_ALLOWED_TOP_KEYS)}"
        )

    table = raw.get("table")
    if not isinstance(table, str) or not table:
        raise ValueError("'table' must be a non-empty string")
    _validate_identifier(table)

    raw_fields = raw.get("fields")
    if not isinstance(raw_fields, list) or not raw_fields:
        raise ValueError("'fields' must be a non-empty list")

    fields = {}
    seen: set[str] = set()
    for spec in raw_fields:
        py_type, field_info = _build_field(spec)
        name = spec["name"]
        if name in seen:
            raise ValueError(f"Duplicate field name '{name}'")
        seen.add(name)
        fields[name] = (py_type, field_info)

    model_name = "".join(p.capitalize() for p in table.split("_")) + "Record"
    model = create_model(model_name, **fields)

    rows_raw = raw.get("rows")
    if rows_raw is None:
        rows = 25
    elif isinstance(rows_raw, int) and rows_raw > 0:
        rows = rows_raw
    else:
        raise ValueError("'rows' must be a positive integer if provided")

    instructions_raw = raw.get("instructions", "") or ""
    if not isinstance(instructions_raw, str):
        raise ValueError("'instructions' must be a string if provided")

    return model, rows, instructions_raw.strip()


def model_from_json(path: str | Path) -> tuple[type[BaseModel], int, str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: '{path}'")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in '{path}': {e}") from e
    return model_from_dict(raw)


def build_batch_model(
    record_model: type[BaseModel], caller: Literal["discovery", "generator"]
) -> type[BaseModel]:
    # Extend the record model with a source field
    enhanced_record = create_model(
        record_model.__name__,
        __base__=record_model,
        source=(Union[str, list[str]], Field(description="Source of the record data")),
    )

    return create_model(
        "RecordBatch",
        records=(
            list[enhanced_record] if caller == "discovery" else list[record_model],
            Field(default_factory=list, description="Generated records"),
        ),
    )
