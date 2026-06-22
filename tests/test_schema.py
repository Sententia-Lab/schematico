from __future__ import annotations

import json
from pathlib import Path

import pytest

from schematico.schema import load_schema, load_schema_from_dict

_USERS = {
    "table": "users",
    "fields": [
        {"name": "id", "type": "uuid"},
        {
            "name": "role",
            "type": "enum",
            "values": ["admin", "editor", "viewer"],
        },
    ],
}


def test_load_schema_from_dict_basic() -> None:
    s = load_schema_from_dict(_USERS)
    assert s.table == "users"
    assert len(s.fields) == 2
    assert s.instructions == ""


def test_instructions_field_parsed() -> None:
    raw = dict(_USERS)
    raw["instructions"] = "  Prefer realistic SaaS email domains.  "
    s = load_schema_from_dict(raw)
    assert s.instructions == "Prefer realistic SaaS email domains."


def test_instructions_must_be_string() -> None:
    raw = dict(_USERS)
    raw["instructions"] = ["nope"]
    with pytest.raises(ValueError):
        load_schema_from_dict(raw)


def test_load_schema_file_round_trip(tmp_path: Path) -> None:
    p = tmp_path / "schema.json"
    p.write_text(json.dumps({**_USERS, "instructions": "Be terse."}))
    s = load_schema(str(p))
    assert s.instructions == "Be terse."
    assert s.table == "users"


def test_count_override_wins() -> None:
    s = load_schema_from_dict(_USERS, count_override=7)
    assert s.rows == 7
