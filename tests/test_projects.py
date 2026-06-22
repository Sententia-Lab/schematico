from __future__ import annotations

from pathlib import Path

import pytest

from schematico.cli import projects


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _make(name: str = "p1", mode: projects.Mode = "discover") -> projects.ProjectConfig:
    return projects.ProjectConfig(
        name=name,
        mode=mode,
        model="gateway/openai:gpt-4.1",
        env_key="MY_KEY",
        output_path="./out.json",
        count=5,
        record_schema={
            "table": "users",
            "fields": [{"name": "id", "type": "uuid"}],
        },
    )


def test_round_trip_toml(workspace: Path) -> None:
    cfg = _make()
    path = projects.save_project(cfg)
    assert path.exists()
    loaded = projects.load_project(path)
    assert loaded.name == cfg.name
    assert loaded.mode == cfg.mode
    assert loaded.model == cfg.model
    assert loaded.env_key == cfg.env_key
    assert loaded.count == 5
    assert loaded.record_schema["table"] == "users"


def test_default_precedence(workspace: Path) -> None:
    projects.save_project(_make("a", "discover"))
    projects.save_project(_make("b", "discover"))
    projects.set_default("discover", "b")

    explicit = projects.resolve_active_project("discover", name_override="a")
    assert explicit.name == "a"

    fallback = projects.resolve_active_project("discover")
    assert fallback.name == "b"


def test_no_default_raises(workspace: Path) -> None:
    with pytest.raises(projects.ProjectNotFoundError):
        projects.resolve_active_project("generate")


def test_missing_named_config_raises(workspace: Path) -> None:
    with pytest.raises(projects.ProjectNotFoundError):
        projects.resolve_active_project("discover", name_override="nope")


def test_next_available_name(workspace: Path) -> None:
    assert projects.next_available_name("project_1", "discover") == "project_1"
    projects.save_project(_make("project_1", "discover"))
    assert projects.next_available_name("project_1", "discover") == "project_1_2"
    projects.save_project(_make("project_1_2", "discover"))
    assert projects.next_available_name("project_1", "discover") == "project_1_3"


def test_list_projects_filters_by_mode(workspace: Path) -> None:
    projects.save_project(_make("a", "discover"))
    projects.save_project(_make("b", "generate"))
    projects.save_state(
        {"discover_default": "a"}
    )  # ensure state.toml exists and is excluded
    disc = projects.list_projects("discover")
    gen = projects.list_projects("generate")
    assert [p.name for p in disc] == ["a.discover.toml"]
    assert [p.name for p in gen] == ["b.generate.toml"]


def test_schema_path_round_trip(workspace: Path) -> None:
    cfg = _make()
    cfg.schema_path = "./schemas/users.json"
    cfg.record_schema = {}
    path = projects.save_project(cfg)
    loaded = projects.load_project(path)
    assert loaded.schema_path == "./schemas/users.json"
    assert loaded.record_schema == {}


def test_delete_project_removes_file(workspace: Path) -> None:
    projects.save_project(_make("a", "discover"))
    p = projects.config_path("a", "discover")
    assert p.exists()
    was_default = projects.delete_project("a", "discover")
    assert not p.exists()
    assert was_default is False


def test_delete_project_clears_default(workspace: Path) -> None:
    projects.save_project(_make("a", "discover"))
    projects.set_default("discover", "a")
    was_default = projects.delete_project("a", "discover")
    assert was_default is True
    assert projects.get_default("discover") is None


def test_delete_project_missing_raises(workspace: Path) -> None:
    with pytest.raises(FileNotFoundError):
        projects.delete_project("nope", "discover")


def test_find_projects_by_name(workspace: Path) -> None:
    projects.save_project(_make("dup", "discover"))
    projects.save_project(_make("dup", "generate"))
    projects.save_project(_make("only_d", "discover"))
    assert sorted(projects.find_projects_by_name("dup")) == ["discover", "generate"]
    assert projects.find_projects_by_name("only_d") == ["discover"]
    assert projects.find_projects_by_name("missing") == []


def test_parse_config_filename() -> None:
    assert projects.parse_config_filename("foo.discover.toml") == ("foo", "discover")
    assert projects.parse_config_filename("foo.generate.toml") == ("foo", "generate")
    assert projects.parse_config_filename("foo.toml") is None
    assert projects.parse_config_filename("state.toml") is None
