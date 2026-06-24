from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import typer

from schematico.cli.projects import (
    DEFAULT_COUNT,
    DEFAULT_ENV_KEY,
    Mode,
    ProjectConfig,
    ensure_config_dir,
    next_available_name,
    save_project,
    set_default,
)
from schematico.models import model_from_dict

_TEMPLATE_SCHEMA: dict[str, Any] = {
    "table": "REPLACE_WITH_TABLE_NAME",
    "rows": 25,
    "instructions": "",
    "fields": [
        {"name": "id", "type": "string", "description": "UUID v4"},
        {"name": "full_name", "type": "string", "description": "realistic full name"},
        {"name": "email", "type": "string", "description": "unique work email"},
        {
            "name": "role",
            "type": "enum",
            "values": ["admin", "editor", "viewer"],
        },
        {
            "name": "country",
            "type": "string",
            "description": "ISO 3166-1 alpha-2 country code",
        },
        {
            "name": "created_at",
            "type": "string",
            "description": "ISO 8601 UTC timestamp",
        },
    ],
}


def _setup_schema(name: str, mode: Mode) -> tuple[dict[str, Any], str]:
    """Return (record_schema, schema_path) — exactly one is populated."""
    if typer.confirm("Do you have an existing JSON schema file to use?", default=False):
        path_str = typer.prompt("Path to JSON schema file")
        p = Path(path_str).expanduser()
        if not p.exists():
            typer.echo(f"schematico: error: file not found: {p}", err=True)
            raise typer.Exit(1)
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            typer.echo(f"schematico: error: invalid JSON in '{p}': {e}", err=True)
            raise typer.Exit(1)
        try:
            model_from_dict(raw)
        except ValueError as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)

        embed = typer.confirm(
            "Embed the schema into the config (vs. reference it by path)?",
            default=True,
        )
        if embed:
            typer.echo(
                f"Imported schema from '{p}' ({len(raw.get('fields', []))} fields)."
            )
            return raw, ""
        typer.echo(f"Referencing schema at '{p}'.")
        return {}, str(p)

    tpl = ensure_config_dir() / f"{name}.{mode}.schema.json"
    if tpl.exists() and not typer.confirm(
        f"{tpl} already exists. Overwrite with a fresh template?", default=False
    ):
        typer.echo(f"Keeping existing template at '{tpl}'. Edit it before running.")
        return {}, str(tpl)
    tpl.write_text(json.dumps(_TEMPLATE_SCHEMA, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Created template schema at '{tpl}'.")
    typer.echo(
        "Edit it (replace REPLACE_WITH_TABLE_NAME, adjust fields, "
        "optionally add 'instructions') before running."
    )
    return {}, str(tpl)


def run_wizard() -> Path:
    name_input = typer.prompt("Project name", default="project_1")
    mode_input = (
        typer.prompt("Mode ([d]iscover/[g]enerate)", default="discover").strip().lower()
    )
    if mode_input in ("d", "discover"):
        mode: Mode = "discover"
    elif mode_input in ("g", "generate"):
        mode = "generate"
    else:
        typer.echo(
            f"Invalid mode '{mode_input}'. Use 'd'/'discover' or 'g'/'generate'.",
            err=True,
        )
        raise typer.Exit(1)

    name = next_available_name(name_input, mode)
    if name != name_input:
        typer.echo(f"Name '{name_input}' is taken; using '{name}' instead.")

    output_path = typer.prompt(
        "Default output directory (filename will be <project>_<timestamp>.json)",
        default="./.schematico/output",
    )
    count = typer.prompt("Count (records to generate)", default=DEFAULT_COUNT, type=int)
    model = typer.prompt(
        "Model (e.g. gateway/anthropic:claude-sonnet-4-6; "
        "leave blank to inherit PAI_MODEL)",
        default=os.environ.get("PAI_MODEL", ""),
        show_default=True,
    )
    env_key = typer.prompt(
        "Name of env var that holds your API key (not the key itself; "
        "leave blank for local/keyless models like ollama)",
        default=DEFAULT_ENV_KEY,
    )
    base_url = typer.prompt(
        "Custom base URL (leave blank to use the provider's default; "
        "e.g. http://localhost:11434/v1 for ollama)",
        default="",
        show_default=False,
    )
    logfire_token = ""
    if typer.confirm(
        "Enable Logfire observability? (You'll need a Logfire write token. "
        "Decline to log to stdout only.)",
        default=False,
    ):
        logfire_token = typer.prompt(
            "Paste your Logfire write token (e.g. pylf_v1_...)",
        )

    record_schema, schema_path = _setup_schema(name, mode)

    cfg = ProjectConfig(
        name=name,
        mode=mode,
        model=model,
        env_key=env_key,
        base_url=base_url,
        output_path=output_path,
        count=count,
        logfire_token=logfire_token,
        schema_path=schema_path,
        record_schema=record_schema,
    )
    path = save_project(cfg)
    set_default(mode, name)

    typer.echo("")
    typer.echo(f"Created {path}")
    typer.echo(f"Set as default for `schematico {mode}`.")
    if record_schema:
        typer.echo(f"Run `schematico {mode}` from this directory when ready.")
    else:
        typer.echo(
            f"Edit '{schema_path}', then run `schematico {mode}` from this directory."
        )
    return path


if __name__ == "__main__":
    typer.run(run_wizard)
