from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from schematico.generator import run_generation
from schematico.helpers import _generate_value, _hash_record
from schematico.models import build_batch_model, build_record_model
from schematico.schema import FieldSpec, Schema


def _simple_schema(rows: int = 2) -> Schema:
    return Schema(
        table="users",
        fields=[
            FieldSpec(name="id", type="uuid"),
            FieldSpec(name="email", type="email"),
            FieldSpec(name="role", type="enum", values=["admin", "editor", "viewer"]),
        ],
        rows=rows,
    )


def _mock_agent(batch):
    fake_result = SimpleNamespace(output=batch)
    return SimpleNamespace(run_sync=lambda *a, **kw: fake_result)


def test_run_generation_returns_expected_shape():
    schema = _simple_schema(rows=2)
    record_model = build_record_model(schema)
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
        records = run_generation(schema)

    assert len(records) == 2
    for record in records:
        assert set(record.keys()) == {"id", "email", "role"}
        assert record["role"] in {"admin", "editor", "viewer"}


def test_run_generation_dedupes_output():
    schema = _simple_schema(rows=2)
    record_model = build_record_model(schema)
    batch_model = build_batch_model(record_model)

    duplicate = record_model(id="a", email="a@example.com", role="admin")
    batch = batch_model(records=[duplicate, duplicate])

    with (
        patch("schematico.generator.build_agent", return_value=_mock_agent(batch)),
        patch("schematico.generator.logfire.configure"),
        patch("schematico.generator.logfire.instrument_pydantic_ai"),
    ):
        records = run_generation(schema)

    assert len(records) == 1


def test_hash_record_is_deterministic_and_value_sensitive():
    a = {"id": "1", "email": "x@y.com"}
    b = {"email": "x@y.com", "id": "1"}  # different key order, same content
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
