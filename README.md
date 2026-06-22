# Schematico

Generate realistic synthetic data from a simple JSON schema. Define your fields,
say how many rows you want, get a clean JSON file back — powered by a
[pydantic-ai](https://ai.pydantic.dev/) agent for LLM-driven discovery or
[Faker](https://faker.readthedocs.io/) for pure offline generation.

```bash
uv add schematico       # as a library
pipx install schematico # as a CLI tool
```

---

## Quick Start (CLI)

```bash
# 1. Set the Pydantic AI Gateway key (used by the LLM-backed `discover` mode).
export PYDANTIC_AI_GATEWAY_API_KEY=pylf_v...

# 2. Create a project interactively. You'll be prompted for mode (generate or
#    discover), schema, output dir, count, model, etc. State lives in
#    ./.schematico/.
schematico new

# 3. Run it.
schematico discover    # or: schematico generate
```

By default, output JSON is written to `./.schematico/output/<project>_<timestamp>.json`.
Override per-run with `--output FILE_OR_DIR` and `--count N`.

### Modes

| Mode | What it does | Needs an API key? |
|---|---|---|
| `generate` | Pure Faker-based field generation. Fast, free, fully offline. | No |
| `discover` | LLM agent (Claude by default) produces records given the schema as context. Better for realistic, coherent, domain-specific data. | Yes |

### Command reference

```
schematico new                     # interactive project wizard
schematico list                    # all saved project configs
schematico delete NAME             # delete a config (use -m to disambiguate mode)
schematico generate [PROJECT]      # run generate mode
schematico discover [PROJECT]      # run discover mode
schematico help                    # full command tree
```

`generate` and `discover` use the currently-default project for their mode if you
don't pass `PROJECT`. Pass `--output PATH` and `--count N` to override the saved
defaults.

---

## Library Usage

```python
from schematico.schema import load_schema
from schematico.generator import run_generation

schema = load_schema("schema.json")  # or: load_schema(path, count_override=25)

# LLM-backed discovery agent (what `schematico discover` uses).
# Requires PYDANTIC_AI_GATEWAY_API_KEY in the environment.
records = run_generation(
    schema,
    progress_cb=lambda found, total, event: print(found, total, event),
)
```

`run_generation` automatically retries transient upstream errors (rate-limit,
529 overload, transient 5xx) via pydantic-ai's tenacity-based transport, with
Retry-After header support.

---

## Schema Format

A schema is a JSON file describing the shape of the data to generate:

```json
{
  "table": "users",
  "fields": [
    { "name": "id",         "type": "uuid" },
    { "name": "full_name",  "type": "full_name" },
    { "name": "email",      "type": "email" },
    { "name": "role",       "type": "enum", "values": ["admin", "editor", "viewer"] },
    { "name": "country",    "type": "country" },
    { "name": "created_at", "type": "timestamp" },
    { "name": "score",      "type": "float", "min": 0, "max": 100 },
    { "name": "age",        "type": "int",   "min": 18, "max": 80 }
  ],
  "rows": 1000
}
```

### Supported Field Types

| Type | Output | Notes |
|---|---|---|
| `uuid` | `"a3f24c1d-..."` | UUID v4 |
| `full_name` | `"Evelyn Carter"` | Realistic full name |
| `email` | `"evelyn@example.com"` | Realistic email |
| `enum` | `"admin"` | Random pick from `values` list (required) |
| `country` | `"United States"` | Country name |
| `timestamp` | `"2024-03-15T09:42:11+00:00"` | UTC ISO 8601 |
| `int` / `integer` | `42301` | Random int; optional `min`/`max` (default 0–100,000) |
| `float` / `decimal` | `0.7341` | Random float; optional `min`/`max` (default 0.0–1.0) |
| `string` | `"ocean"` | Random word |
| `boolean` | `true` | Random true/false |

See [`examples/users.json`](examples/users.json) for a working schema.

---

## Configuration

| Env var | Purpose |
|---|---|
| `PYDANTIC_AI_GATEWAY_API_KEY` | Pydantic AI Gateway key (required for `discover` mode). |
| `PAI_MODEL` | LLM model id. Defaults to `gateway/anthropic:claude-sonnet-4-6`. Use any gateway-routed provider, e.g. `gateway/openai:gpt-4.1`. |
| `LOGFIRE_TOKEN` | Optional. If set, traces, tool calls, and token usage are sent to [Logfire](https://pydantic.dev/logfire). |
| `LOG_LEVEL` | `WARNING` (default), `INFO`, or `DEBUG`. Controls stderr verbosity. |

Project configs are stored in `./.schematico/` as `<name>.<mode>.toml` files,
with `state.toml` tracking the active default per mode.

---

## Roadmap

- Second-pass agentic duplicate checker for smarter deduplication
- Output formats: CSV, Excel, SQL, Parquet
- Real data discovery mode (web search / external sources, not just synthetic)

---

## License

MIT. See [`LICENSE`](LICENSE).

Contributing? See [`README.dev.md`](README.dev.md).
