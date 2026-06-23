from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from schematico.cli.progress import ProgressReporter
from schematico.cli.projects import ProjectConfig
from schematico.generator import run_generation
from schematico.logging import get_logger
from schematico.models import build_record_model
from schematico.providers import DEFAULT_MODEL, env_key_for
from schematico.schema import load_schema, load_schema_from_dict

logger = get_logger("cli.runner")


def run(
    config: ProjectConfig,
    *,
    output_override: str | None = None,
    count_override: int | None = None,
    model_override: str | None = None,
) -> None:
    if not config.record_schema and not config.schema_path:
        print(
            f"schematico: error: config '{config.name}.{config.mode}.toml' has no "
            "schema. Either fill the [schema] table or set schema_path "
            f"(e.g. `schematico {config.mode} schema import ./schema.json`).",
            file=sys.stderr,
        )
        sys.exit(1)

    model = model_override or config.model or None
    resolved_model = model or DEFAULT_MODEL
    env_key = env_key_for(resolved_model) or config.env_key
    if env_key and not os.environ.get(env_key):
        print(
            f"schematico: error: env var '{env_key}' is not set "
            f"(required by model '{resolved_model}').",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        if config.schema_path:
            spec = load_schema(config.schema_path)
            raw = json.loads(Path(config.schema_path).read_text(encoding="utf-8"))
        else:
            spec = load_schema_from_dict(config.record_schema)
            raw = config.record_schema
    except (FileNotFoundError, ValueError) as e:
        print(f"schematico: error: {e}", file=sys.stderr)
        sys.exit(1)

    samples = (
        count_override
        if count_override is not None
        else (raw.get("rows") if isinstance(raw.get("rows"), int) else config.count)
    )
    instructions = spec.instructions
    record_model = build_record_model(spec)
    output_path = output_override or config.output_path

    logger.info(
        "Running %s for '%s': %d fields, %d records, model=%s",
        config.mode,
        spec.table,
        len(spec.fields),
        samples,
        model or "(default)",
    )

    from pydantic_ai.exceptions import UserError

    reporter = ProgressReporter(spec.table)
    try:
        records = run_generation(
            record_model,
            samples,
            instructions,
            progress_cb=reporter.update,
            model=model,
            logfire_token=config.logfire_token or None,
        )
    except UserError as e:
        print(f"schematico: error: {e}", file=sys.stderr)
        sys.exit(1)
    reporter.done(len(records))

    out_path = Path(output_path)
    if out_path.suffix:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out = out_path
    else:
        out_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out_path / f"{config.name}_{timestamp}.json"
    try:
        with out.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"schematico: error writing output: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("Wrote %d records to %s", len(records), out)
    print(f"Generated {len(records)} records " f"from schema '{spec.table}' -> {out}")
