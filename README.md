<p align="center">
  <img src="https://raw.githubusercontent.com/Sententia-Lab/schematico/main/assets/logo.svg" alt="Schematico" width="110" />
</p>

<h1 align="center">Schematico</h1>

<p align="center">
  <strong>Describe the data you want. Get it back as clean JSON.</strong><br/>
  Find real public records on the live web, or synthesize realistic ones — from one tiny schema.
</p>

<p align="center">
  <a href="https://pypi.org/project/schematico/"><img src="https://img.shields.io/pypi/v/schematico.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/schematico/"><img src="https://img.shields.io/pypi/pyversions/schematico.svg" alt="Python versions"></a>
  <a href="https://github.com/Sententia-Lab/schematico/actions/workflows/test.yml"><img src="https://github.com/Sententia-Lab/schematico/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
</p>

---

## Why Schematico exists

Schematico started with a frustration: the public data I needed was *out there*,
but never in a form I could use. Congressional race results, public filings,
sports stats, niche reference tables — scattered across a dozen sites, trapped in
HTML, or sitting behind a paywall. Getting a clean table meant hours of copy-paste,
fragile scrapers, and manual cleanup.

So I built a tool where you describe the shape of the data you want — once, in a
few lines — and let an AI agent go **find it on the live web** and hand it back as
structured JSON.

One schema. Two ways to fill it.

| Mode | What it does | Needs |
|---|---|---|
| **`discover`** | An AI agent searches the live web (via [Tavily](https://tavily.com)) and returns **real** records matching your schema. | LLM key + `TAVILY_API_KEY` |
| **`generate`** | An LLM **synthesizes** realistic, coherent records from your schema — no web access, fully made-up data. | LLM key |

> Both modes are LLM-backed. Output is always validated against your schema and
> de-duplicated before you get it.

---

## Install

```bash
pipx install schematico   # as a CLI tool
uv add schematico         # as a library
pip install schematico    # the classic way
```
---

## Library usage

Define a schema as a Pydantic model and call `run_generation` or `run_discovery`:

```python
from pydantic import BaseModel, Field
from schematico import run_generation

class User(BaseModel):
    id: str = Field(description="UUID v4")
    full_name: str = Field(description="realistic full name")
    email: str = Field(description="work email matching the name")
    role: str = Field(description="one of: admin, editor, viewer")

records = run_generation(
    User,
    samples=10,
    instructions="EU-based users only. Emails must match the full_name.",
)
# -> list[dict], validated and de-duplicated
```

Prefer JSON schemas? Load one and run it:

```python
from schematico import model_from_json, run_generation

model, rows, instructions = model_from_json("schema.json")
records = run_generation(model, samples=rows, instructions=instructions)
```

To find **real** data on the web instead, swap in `run_discovery` (needs
`TAVILY_API_KEY`):

```python
from schematico import run_discovery
records = run_discovery(User, samples=25, instructions="...")
```

Both functions accept an optional `progress_cb(found, total, event)` callback and
a `logfire_token` for tracing.

---

## Bring your own models

Schematico runs on [pydantic-ai](https://ai.pydantic.dev/), so you can point it
at virtually any model — hosted, gateway-routed, or local — and even build a
**failover chain** that tries each in order.

```python
from schematico import SchematicoModel, get_llm_model, run_discovery

model = get_llm_model([
    # try the gateway first…
    SchematicoModel(model="gateway/anthropic:claude-sonnet-4-6"),
    # …fall back to a direct provider…
    SchematicoModel(model="openai:gpt-4.1", api_key="sk-..."),
    # …then a local, keyless model.
    SchematicoModel(model="ollama:llama3.2", base_url="http://localhost:11434/v1"),
])

records = run_discovery(MySchema, samples=50, model=model)
```

- A bare model string (`"anthropic:claude-sonnet-4-6"`) reads credentials from the
  provider's usual env var.
- A `SchematicoModel` lets you pin `api_key` and `base_url` per model.
- A list becomes an automatic failover chain.

From the CLI, set the model per project (`schematico new`, or
`schematico <mode> use model <id>`) and the env var that holds its key.

---

## Quick start (CLI)

```bash
# 1. Point Schematico at a model. The default routes Claude through the
#    Pydantic AI Gateway — set its key (or see "Bring your own models" below).
export PYDANTIC_AI_GATEWAY_API_KEY=...

# 2. For discover mode, add a Tavily key (free tier at https://tavily.com).
export TAVILY_API_KEY=...

# 3. Create a project interactively. You'll be prompted for mode, schema,
#    output dir, count, and model. State lives in ./.schematico/.
schematico new

# 4. Run it.
schematico discover     # find real records on the web
# or
schematico generate     # synthesize records
```

Output is written to `./.schematico/output/<project>_<timestamp>.json` by default.
Override per run with `--output FILE_OR_DIR` and `--count N`.

### Command reference

```
schematico new                     # interactive project wizard
schematico list                    # all saved project configs
schematico generate [--config N]   # synthesize records (uses default project)
schematico discover [--config N]   # find real records on the web
schematico delete NAME             # delete a config (-m to disambiguate mode)
schematico help                    # the full command tree, every flag
```

Common flags on `generate` / `discover`: `--config/-c`, `--output/-o`,
`--count/-n`, `--model/-m`.

---

## Schema format

A schema is a small JSON object describing the table you want:

```json
{
  "table": "congressional_elections",
  "rows": 50,
  "instructions": "U.S. House races in the 2026 midterms.",
  "fields": [
    { "name": "district",        "type": "string", "description": "state and district, e.g. 'CA-12'" },
    { "name": "election_date",   "type": "string", "description": "ISO 8601 date" },
    { "name": "incumbent_party", "type": "enum",   "values": ["D", "R", "I"] },
    { "name": "is_open_seat",    "type": "bool" }
  ]
}
```

| Top-level key | Required | Meaning |
|---|---|---|
| `table` | ✅ | Name of the table (also names the output model). |
| `fields` | ✅ | List of field definitions (see below). |
| `rows` | — | How many records to produce (default `25`). |
| `instructions` | — | Free-text guidance passed to the agent. |

### Field types

Types are deliberately minimal — the **`description`** does the heavy lifting.

| Type | Python | Notes |
|---|---|---|
| `string` | `str` | Any text. Shape it with `description`, e.g. `"UUID v4"`, `"ISO 8601 timestamp"`, `"ISO 3166 country code"`. |
| `int` | `int` | Optional `min` / `max`. |
| `float` | `float` | Optional `min` / `max`. |
| `bool` | `bool` | `true` / `false`. |
| `enum` | one of `values` | Requires a non-empty `values` list. |

> There's no dedicated `uuid` / `email` / `timestamp` type on purpose. Use
> `string` and say what you want in `description` — the model fills it in
> accordingly, and you're never boxed in by a fixed type list.

---

## Configuration

| Env var | Purpose |
|---|---|
| `PYDANTIC_AI_GATEWAY_API_KEY` | Key for the default gateway-routed model. |
| `PAI_MODEL` | Override the default model id (`gateway/anthropic:claude-sonnet-4-6`). |
| `TAVILY_API_KEY` | Required for `discover` mode (live web search). |
| `LOGFIRE_TOKEN` | Optional. Send traces, tool calls, and token usage to [Logfire](https://pydantic.dev/logfire). |
| `LOG_LEVEL` | `WARNING` (default), `INFO`, or `DEBUG`. |

Schematico auto-loads a `.env` file from the current directory — see
[`.env.example`](.env.example). Project configs live in `./.schematico/` as
`<name>.<mode>.toml` files.

---

## Coming soon

Schematico is just getting started. On the roadmap:

- 📦 **More output formats** — CSV, Excel, SQL inserts, and Parquet, not just JSON.
- 🔎 **Smarter discovery** — source citations per record, deeper crawling, and a
  second-pass agent that verifies and de-duplicates findings.
- 🧩 **Richer schemas** — nested objects, relationships between tables, and
  reusable field presets.
- 🗄️ **Direct sinks** — write straight into a database or a dataframe.
- ⚡ **Offline generation** — a fast, keyless synthesis mode for when you don't
  want to call a model at all.

Have an idea? [Open an issue](https://github.com/Sententia-Lab/schematico/issues) —
this is the moment to shape where it goes.

---

## Contributing

Contributions are very welcome — issues, docs, and PRs all help. See
[CONTRIBUTING.md](CONTRIBUTING.md) to get from clone to PR in a couple of minutes.
The test suite mocks the LLM, so `uv run pytest` needs no API keys.

## License

MIT. See [`LICENSE`](LICENSE).
