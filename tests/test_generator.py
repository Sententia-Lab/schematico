from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from pydantic import BaseModel, Field

from schematico.generator import run_generation
from schematico.helpers import _generate_value, _hash_record
from schematico.models import build_batch_model, build_record_model
from schematico.schema import FieldSpec, Schema


def _simple_schema() -> Schema:
    return Schema(
        table="users",
        fields=[
            FieldSpec(name="id", type="uuid"),
            FieldSpec(name="email", type="email"),
            FieldSpec(name="role", type="enum", values=["admin", "editor", "viewer"]),
        ],
        rows=2,
    )


def _mock_agent(batch):
    fake_result = SimpleNamespace(output=batch)
    return SimpleNamespace(run_sync=lambda *a, **kw: fake_result)


def test_run_generation_returns_expected_shape():
    record_model = build_record_model(_simple_schema())
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
    record_model = build_record_model(_simple_schema())
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


def test_generate_value_respects_field_type():
    assert isinstance(_generate_value(FieldSpec(name="id", type="uuid")), str)
    assert _generate_value(
        FieldSpec(name="role", type="enum", values=["admin", "viewer"])
    ) in {"admin", "viewer"}

    n = _generate_value(FieldSpec(name="age", type="int", min=10, max=12))
    assert isinstance(n, int) and 10 <= n <= 12

    b = _generate_value(FieldSpec(name="flag", type="boolean"))
    assert isinstance(b, bool)
