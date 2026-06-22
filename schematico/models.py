from __future__ import annotations

from pydantic import BaseModel, Field, create_model

from schematico.schema import Schema

TYPE_MAP: dict[str, type] = {
    "uuid": str,
    "full_name": str,
    "email": str,
    "enum": str,
    "country": str,
    "timestamp": str,
    "string": str,
    "int": int,
    "integer": int,
    "boolean": bool,
    "float": float,
    "decimal": float,
}


def build_record_model(schema: Schema) -> type[BaseModel]:
    fields: dict[str, tuple[type, object]] = {}

    for f in schema.fields:
        py_type = TYPE_MAP[f.type]
        description = f"Field '{f.name}' of type {f.type}"
        if f.values:
            description += f". Must be exactly one of: {f.values}"
        if f.min is not None or f.max is not None:
            description += f". Must be in range {f.min} to {f.max}"
        fields[f.name] = (py_type, Field(description=description))

    model_name = "".join(part.capitalize() for part in schema.table.split("_"))
    return create_model(f"{model_name}Record", **fields)


def build_batch_model(record_model: type[BaseModel]) -> type[BaseModel]:
    return create_model(
        "RecordBatch",
        records=(
            list[record_model],
            Field(default_factory=list, description="Generated records"),
        ),
    )
