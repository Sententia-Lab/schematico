from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any, Literal

import tomli_w
from pydantic import BaseModel, ConfigDict, Field

Mode = Literal["generate", "discover"]
MODES: tuple[Mode, ...] = ("generate", "discover")

CONFIG_DIRNAME = ".schematico"
STATE_FILENAME = "state.toml"
DEFAULT_ENV_KEY = "PYDANTIC_AI_GATEWAY_API_KEY"
DEFAULT_COUNT = 25


class ProjectConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    name: str
    mode: Mode
    model: str = ""
    env_key: str = DEFAULT_ENV_KEY
    base_url: str = ""
    output_path: str = f"./{CONFIG_DIRNAME}/output"
    count: int = DEFAULT_COUNT
    logfire_token: str = ""
    schema_path: str = ""
    record_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")


def config_dir(cwd: Path | None = None) -> Path:
    base = cwd if cwd is not None else Path.cwd()
    return base / CONFIG_DIRNAME


def ensure_config_dir(cwd: Path | None = None) -> Path:
    d = config_dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_filename(name: str, mode: Mode) -> str:
    return f"{name}.{mode}.toml"


def config_path(name: str, mode: Mode, cwd: Path | None = None) -> Path:
    return config_dir(cwd) / config_filename(name, mode)


def state_path(cwd: Path | None = None) -> Path:
    return config_dir(cwd) / STATE_FILENAME


def load_state(cwd: Path | None = None) -> dict[str, str]:
    p = state_path(cwd)
    if not p.exists():
        return {}
    with p.open("rb") as f:
        return tomllib.load(f)


def save_state(state: dict[str, str], cwd: Path | None = None) -> None:
    ensure_config_dir(cwd)
    p = state_path(cwd)
    with p.open("wb") as f:
        tomli_w.dump(state, f)


def get_default(mode: Mode, cwd: Path | None = None) -> str | None:
    return load_state(cwd).get(f"{mode}_default")


def set_default(mode: Mode, name: str, cwd: Path | None = None) -> None:
    state = load_state(cwd)
    state[f"{mode}_default"] = name
    save_state(state, cwd)


def clear_default(mode: Mode, cwd: Path | None = None) -> bool:
    state = load_state(cwd)
    key = f"{mode}_default"
    if key not in state:
        return False
    del state[key]
    save_state(state, cwd)
    return True


def delete_project(name: str, mode: Mode, cwd: Path | None = None) -> bool:
    """Delete the config file and clear the mode default if it pointed here.

    Returns True if the deleted project was the current default for its mode.
    Raises FileNotFoundError if no such config exists.
    """
    p = config_path(name, mode, cwd)
    if not p.exists():
        raise FileNotFoundError(p)
    p.unlink()
    if get_default(mode, cwd) == name:
        clear_default(mode, cwd)
        return True
    return False


def find_projects_by_name(name: str, cwd: Path | None = None) -> list[Mode]:
    """Return modes that have a project with the given name."""
    return [m for m in MODES if config_path(name, m, cwd).exists()]


def load_project(path: Path) -> ProjectConfig:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return ProjectConfig(**raw)


def save_project(config: ProjectConfig, cwd: Path | None = None) -> Path:
    ensure_config_dir(cwd)
    p = config_path(config.name, config.mode, cwd)
    data = config.model_dump(by_alias=True)
    with p.open("wb") as f:
        tomli_w.dump(data, f)
    return p


def list_projects(mode: Mode | None = None, cwd: Path | None = None) -> list[Path]:
    d = config_dir(cwd)
    if not d.exists():
        return []
    suffix = f".{mode}.toml" if mode else ".toml"
    return sorted(
        p for p in d.iterdir() if p.name.endswith(suffix) and p.name != STATE_FILENAME
    )


def parse_config_filename(filename: str) -> tuple[str, Mode] | None:
    m = re.fullmatch(r"(.+)\.(generate|discover)\.toml", filename)
    if not m:
        return None
    return m.group(1), m.group(2)  # type: ignore[return-value]


def next_available_name(base: str, mode: Mode, cwd: Path | None = None) -> str:
    if not config_path(base, mode, cwd).exists():
        return base
    n = 2
    while config_path(f"{base}_{n}", mode, cwd).exists():
        n += 1
    return f"{base}_{n}"


class ProjectNotFoundError(Exception):
    pass


def resolve_active_project(
    mode: Mode,
    name_override: str | None = None,
    cwd: Path | None = None,
) -> ProjectConfig:
    name = name_override or get_default(mode, cwd)
    if not name:
        raise ProjectNotFoundError(
            f"No active {mode} project. Run `schematico new` to create one, "
            f"or `schematico {mode} use <name>` to select an existing config."
        )
    p = config_path(name, mode, cwd)
    if not p.exists():
        raise ProjectNotFoundError(f"Config '{p.name}' not found in {config_dir(cwd)}.")
    return load_project(p)
