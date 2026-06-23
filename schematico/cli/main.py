from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

from schematico.cli import runner
from schematico.cli.projects import (
    Mode,
    ProjectNotFoundError,
    config_path,
    delete_project,
    find_projects_by_name,
    get_default,
    list_projects,
    parse_config_filename,
    resolve_active_project,
    save_project,
    set_default,
)
from schematico.cli.wizard import run_wizard
from schematico.logging import get_logger

load_dotenv()
logger = get_logger("cli.main")

app = typer.Typer(
    name="schematico",
    help=(
        "Generate or discover synthetic data from a JSON schema.\n\n"
        "Run `schematico help` to see every command and flag in one place."
    ),
    no_args_is_help=True,
    add_completion=False,
)


def _make_mode_app(mode: Mode) -> typer.Typer:
    sub = typer.Typer(
        name=mode,
        help=f"{mode.capitalize()} records using a project config.",
        invoke_without_command=True,
        no_args_is_help=False,
    )

    @sub.callback()
    def _default(
        ctx: typer.Context,
        config: str | None = typer.Option(
            None,
            "--config",
            "-c",
            help="Project config name to use (overrides default).",
        ),
        output_path: str | None = typer.Option(
            None, "--output", "-o", help="Override output path."
        ),
        count: int | None = typer.Option(
            None, "--count", "-n", help="Override record count."
        ),
        model: str | None = typer.Option(
            None, "--model", "-m", help="Override AI model."
        ),
    ) -> None:
        if ctx.invoked_subcommand is not None:
            ctx.obj = {"config": config}
            return
        try:
            cfg = resolve_active_project(mode, name_override=config)
        except ProjectNotFoundError as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)
        runner.run(
            cfg,
            output_override=output_path,
            count_override=count,
            model_override=model,
        )

    @sub.command("list", help=f"List {mode} configs.")
    def _list() -> None:
        default_name = get_default(mode)
        paths = list_projects(mode)
        if not paths:
            typer.echo(f"No {mode} configs found in ./.schematico/.")
            typer.echo("Run `schematico new` to create one.")
            return
        for p in paths:
            parsed = parse_config_filename(p.name)
            name = parsed[0] if parsed else p.name
            marker = "*" if name == default_name else " "
            typer.echo(f"{marker} {name}  ({p})")

    @sub.command(
        "use",
        help=f"Select default {mode} config (`use <name>`) or set model (`use model <id>`).",
    )
    def _use(args: list[str] = typer.Argument(None)) -> None:
        if not args:
            typer.echo(
                f"Usage: schematico {mode} use <name> | use model <id>", err=True
            )
            raise typer.Exit(2)
        if args[0] == "model":
            if len(args) != 2:
                typer.echo(f"Usage: schematico {mode} use model <id>", err=True)
                raise typer.Exit(2)
            try:
                cfg = resolve_active_project(mode)
            except ProjectNotFoundError as e:
                typer.echo(f"schematico: error: {e}", err=True)
                raise typer.Exit(1)
            cfg.model = args[1]
            save_project(cfg)
            typer.echo(f"Set model={args[1]} in '{cfg.name}.{mode}.toml'.")
            return
        if len(args) != 1:
            typer.echo(f"Usage: schematico {mode} use <name>", err=True)
            raise typer.Exit(2)
        name = args[0]
        if not config_path(name, mode).exists():
            typer.echo(
                f"schematico: error: config '{name}.{mode}.toml' not found.", err=True
            )
            raise typer.Exit(1)
        set_default(mode, name)
        typer.echo(f"Default {mode} config set to '{name}'.")

    @sub.command("delete", help=f"Delete a {mode} config.")
    def _delete(
        name: str = typer.Argument(...),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    ) -> None:
        p = config_path(name, mode)
        if not p.exists():
            typer.echo(
                f"schematico: error: config '{name}.{mode}.toml' not found.",
                err=True,
            )
            raise typer.Exit(1)
        if not yes and not typer.confirm(f"Delete {p}?", default=False):
            typer.echo("Aborted.")
            raise typer.Exit(0)
        was_default = delete_project(name, mode)
        msg = f"Deleted '{name}.{mode}.toml'."
        if was_default:
            msg += f" Cleared default for `schematico {mode}`."
        typer.echo(msg)

    @sub.command("output")
    def _set_output(path: str = typer.Argument(...)) -> None:
        try:
            cfg = resolve_active_project(mode)
        except ProjectNotFoundError as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)
        cfg.output_path = path
        save_project(cfg)
        typer.echo(f"Set output_path={path} in '{cfg.name}.{mode}.toml'.")

    schema_app = typer.Typer(
        help="Manage the schema for the active config (`import` or `path`).",
        no_args_is_help=True,
    )

    @schema_app.command("import")
    def _schema_import(file: str = typer.Argument(..., help="Path to a JSON schema file.")) -> None:
        """Embed a JSON schema file into the active config's [schema] table."""
        import json as _json

        from schematico.models import model_from_dict

        try:
            cfg = resolve_active_project(mode)
        except ProjectNotFoundError as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)
        p = Path(file)
        if not p.exists():
            typer.echo(f"schematico: error: file '{file}' not found.", err=True)
            raise typer.Exit(1)
        try:
            raw = _json.loads(p.read_text(encoding="utf-8"))
        except _json.JSONDecodeError as e:
            typer.echo(f"schematico: error: invalid JSON in '{file}': {e}", err=True)
            raise typer.Exit(1)
        try:
            model_from_dict(raw)
        except ValueError as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)
        cfg.record_schema = raw
        cfg.schema_path = ""
        save_project(cfg)
        typer.echo(
            f"Imported schema from '{file}' into '{cfg.name}.{mode}.toml' "
            f"({len(raw.get('fields', []))} fields)."
        )

    @schema_app.command("path")
    def _schema_path(file: str = typer.Argument(..., help="Path to a JSON schema file to reference.")) -> None:
        """Reference an external JSON schema file (not embedded)."""
        from schematico.models import model_from_json

        try:
            cfg = resolve_active_project(mode)
        except ProjectNotFoundError as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)
        try:
            model_from_json(file)
        except (FileNotFoundError, ValueError) as e:
            typer.echo(f"schematico: error: {e}", err=True)
            raise typer.Exit(1)
        cfg.schema_path = file
        cfg.record_schema = {}
        save_project(cfg)
        typer.echo(f"Set schema_path={file} in '{cfg.name}.{mode}.toml'.")

    sub.add_typer(schema_app, name="schema")

    return sub


app.add_typer(_make_mode_app("generate"), name="generate")
app.add_typer(_make_mode_app("discover"), name="discover")


@app.command("new")
def new_cmd() -> None:
    """Interactively create a new project config."""
    run_wizard()


@app.command("delete", help="Delete a project config by name (auto-detects mode).")
def delete_cmd(
    name: str = typer.Argument(..., help="Project name (without .toml suffix)."),
    mode: str | None = typer.Option(
        None,
        "--mode",
        "-m",
        help="Required when the name exists for both `generate` and `discover`.",
    ),
    all_modes: bool = typer.Option(
        False, "--all", "-a", help="Delete the project for every mode it exists in."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    matches = find_projects_by_name(name)
    if not matches:
        typer.echo(f"schematico: error: no project named '{name}'.", err=True)
        raise typer.Exit(1)

    if mode is not None:
        if mode not in ("generate", "discover"):
            typer.echo(
                f"schematico: error: --mode must be 'generate' or 'discover'.",
                err=True,
            )
            raise typer.Exit(2)
        if mode not in matches:
            typer.echo(
                f"schematico: error: no {mode} project named '{name}'.", err=True
            )
            raise typer.Exit(1)
        targets: list[Mode] = [mode]  # type: ignore[list-item]
    elif all_modes:
        targets = matches
    elif len(matches) == 1:
        targets = matches
    else:
        typer.echo(
            f"schematico: error: '{name}' exists for both modes "
            f"({', '.join(matches)}). Pass --mode <generate|discover> or --all.",
            err=True,
        )
        raise typer.Exit(1)

    paths = [config_path(name, m) for m in targets]
    if not yes:
        typer.echo("About to delete:")
        for p in paths:
            typer.echo(f"  - {p}")
        if not typer.confirm("Proceed?", default=False):
            typer.echo("Aborted.")
            raise typer.Exit(0)

    for m in targets:
        was_default = delete_project(name, m)
        msg = f"Deleted '{name}.{m}.toml'."
        if was_default:
            msg += f" Cleared default for `schematico {m}`."
        typer.echo(msg)


@app.command("list")
def list_cmd() -> None:
    """List all schematico project configs (both discover and generate)."""
    rows: list[tuple[str, str, str, str]] = []  # (marker, mode, name, path)
    for mode in ("discover", "generate"):
        default_name = get_default(mode)  # type: ignore[arg-type]
        for p in list_projects(mode):  # type: ignore[arg-type]
            parsed = parse_config_filename(p.name)
            name = parsed[0] if parsed else p.name
            marker = "*" if name == default_name else " "
            rows.append((marker, mode, name, str(p)))

    if not rows:
        typer.echo("No project configs found in ./.schematico/.")
        typer.echo("Run `schematico new` to create one.")
        return

    mode_w = max(len(r[1]) for r in rows)
    name_w = max(len(r[2]) for r in rows)
    for marker, mode, name, path in rows:
        typer.echo(f"{marker} [{mode:<{mode_w}}]  {name:<{name_w}}  ({path})")


def _walk_help(cmd, ctx, path: str) -> None:
    import click

    typer.echo("")
    typer.echo("=" * 72)
    typer.echo(path)
    typer.echo("=" * 72)
    typer.echo(cmd.get_help(ctx))
    if isinstance(cmd, click.Group):
        for name, sub in cmd.commands.items():
            sub_ctx = click.Context(sub, info_name=name, parent=ctx)
            _walk_help(sub, sub_ctx, f"{path} {name}")


@app.command("help")
def help_cmd() -> None:
    """Show help for every command and subcommand (full tree)."""
    import click
    from typer.main import get_command

    cli = get_command(app)
    ctx = click.Context(cli, info_name="schematico")
    _walk_help(cli, ctx, "schematico")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
