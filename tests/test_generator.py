from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from schematico.generator import _hash_record, run_generation
from schematico.models import build_batch_model, model_from_dict


_USERS_SCHEMA = {
    "table": "users",
    "rows": 2,
    "fields": [
        {"name": "id", "type": "string", "description": "UUID v4"},
        {"name": "email", "type": "string", "description": "unique work email"},
        {"name": "role", "type": "enum", "values": ["admin", "editor", "viewer"]},
    ],
}


def _mock_agent(batch):
    fake_result = SimpleNamespace(output=batch)
    return SimpleNamespace(run_sync=lambda *a, **kw: fake_result)


def test_run_generation_returns_expected_shape():
    record_model, _rows, _instructions = model_from_dict(_USERS_SCHEMA)
    batch_model = build_batch_model(record_model)
    batch = batch_model(
        records=[
            record_model(id="a", email="a@example.com", role="admin"),
            record_model(id="b", email="b@example.com", role="viewer"),
        ]
    )

    with (
        patch("schematico.generator.build_agent", return_value=_mock_agent(batch)),
        patch("schematico.generator.logfire.configure"),
        patch("schematico.generator.logfire.instrument_pydantic_ai"),
    ):
        records = run_generation(record_model, samples=2, instructions="")

    assert len(records) == 2
    for record in records:
        assert set(record.keys()) == {"id", "email", "role"}
        assert record["role"] in {"admin", "editor", "viewer"}


def test_run_generation_dedupes_output():
    record_model, _rows, _instructions = model_from_dict(_USERS_SCHEMA)
    batch_model = build_batch_model(record_model)
    duplicate = record_model(id="a", email="a@example.com", role="admin")
    batch = batch_model(records=[duplicate, duplicate])

    with (
        patch("schematico.generator.build_agent", return_value=_mock_agent(batch)),
        patch("schematico.generator.logfire.configure"),
        patch("schematico.generator.logfire.instrument_pydantic_ai"),
    ):
        records = run_generation(record_model, samples=2)

    assert len(records) == 1


def test_run_generation_accepts_user_pydantic_model():
    class Users(BaseModel):
        id: str = Field(description="UUID v4")
        email: str = Field(description="unique work email")

    batch_model = build_batch_model(Users)
    batch = batch_model(
        records=[
            Users(id="a", email="a@example.com"),
            Users(id="b", email="b@example.com"),
        ]
    )

    with (
        patch("schematico.generator.build_agent", return_value=_mock_agent(batch)),
        patch("schematico.generator.logfire.configure"),
        patch("schematico.generator.logfire.instrument_pydantic_ai"),
    ):
        records = run_generation(
            Users, samples=2, instructions="EU-based users only"
        )

    assert len(records) == 2
    assert {"id", "email"} == set(records[0].keys())


def test_hash_record_is_deterministic_and_value_sensitive():
    a = {"id": "1", "email": "x@y.com"}
    b = {"email": "x@y.com", "id": "1"}
    c = {"id": "1", "email": "x@z.com"}

    assert _hash_record(a) == _hash_record(b)
    assert _hash_record(a) != _hash_record(c)


# --- model_from_dict contract ---


def test_model_from_dict_basic():
    model, rows, instructions = model_from_dict(_USERS_SCHEMA)
    assert model.__name__ == "UsersRecord"
    assert set(model.model_fields) == {"id", "email", "role"}
    assert rows == 2
    assert instructions == ""


def test_model_from_dict_default_rows():
    raw = {"table": "t", "fields": [{"name": "x", "type": "string"}]}
    _, rows, _ = model_from_dict(raw)
    assert rows == 25


def test_model_from_dict_strips_instructions():
    raw = {
        "table": "t",
        "fields": [{"name": "x", "type": "string"}],
        "instructions": "  be terse  ",
    }
    _, _, instructions = model_from_dict(raw)
    assert instructions == "be terse"


def test_model_from_dict_rejects_unknown_top_key():
    raw = {"table": "t", "fields": [{"name": "x", "type": "string"}], "row": 5}
    with pytest.raises(ValueError, match="Unknown top-level keys"):
        model_from_dict(raw)


def test_model_from_dict_rejects_unknown_field_key():
    raw = {
        "table": "t",
        "fields": [{"name": "x", "type": "string", "format": "uuid"}],
    }
    with pytest.raises(ValueError, match="unknown keys"):
        model_from_dict(raw)


def test_model_from_dict_rejects_invalid_identifier():
    raw = {"table": "t", "fields": [{"name": "1bad", "type": "string"}]}
    with pytest.raises(ValueError, match="valid Python identifier"):
        model_from_dict(raw)


def test_model_from_dict_rejects_python_keyword():
    raw = {"table": "t", "fields": [{"name": "class", "type": "string"}]}
    with pytest.raises(ValueError, match="valid Python identifier"):
        model_from_dict(raw)


def test_model_from_dict_enum_requires_values():
    raw = {"table": "t", "fields": [{"name": "x", "type": "enum"}]}
    with pytest.raises(ValueError, match="enum requires"):
        model_from_dict(raw)


def test_model_from_dict_min_max_only_for_numeric():
    raw = {
        "table": "t",
        "fields": [{"name": "x", "type": "string", "min": 1}],
    }
    with pytest.raises(ValueError, match="'min' only valid"):
        model_from_dict(raw)


def test_model_from_dict_enforces_numeric_range():
    raw = {
        "table": "t",
        "fields": [{"name": "age", "type": "int", "min": 18, "max": 99}],
    }
    model, _, _ = model_from_dict(raw)
    model(age=42)
    with pytest.raises(Exception):
        model(age=5)


def test_model_from_dict_enum_constrains_values():
    raw = {
        "table": "t",
        "fields": [
            {"name": "role", "type": "enum", "values": ["a", "b"]},
        ],
    }
    model, _, _ = model_from_dict(raw)
    model(role="a")
    with pytest.raises(Exception):
        model(role="c")
