# Contributing to Schematico

First off — thank you. Schematico is young and open, and every issue, idea, and
pull request genuinely helps. This guide will get you from clone to PR in a few
minutes.

## Ways to contribute

- **Report a bug** — open an issue with steps to reproduce.
- **Request a feature** — open an issue describing the problem you're trying to
  solve (the *why* matters more than the *how*).
- **Improve the docs** — typos, clearer examples, and better explanations are
  always welcome.
- **Write code** — pick up an open issue, or propose a change. For anything
  large, open an issue first so we can agree on direction before you invest time.

## Development setup

Schematico uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/Sententia-Lab/schematico.git
cd schematico
uv sync                       # installs the package + dev tools into .venv

cp .env.example .env          # add any keys you need (most tests need none)
```

## Running the tests

```bash
uv run pytest                 # the full suite — runs in ~2s, no API keys needed
```

The test suite mocks the LLM, so you don't need credentials or network access to
run it. Please add tests for any new behavior.

## Code style

```bash
uv run black .                # format before committing
```

- Keep functions small and typed — the codebase uses modern type hints throughout.
- Match the style of the surrounding code.
- New public functions get a short docstring.

## Submitting a pull request

1. Fork the repo and create a branch off `main`
   (`git checkout -b feature/my-change`).
2. Make your change, with tests, and run `uv run pytest` + `uv run black .`.
3. Write a clear PR description: what changed, and why.
4. Open the PR against `main`. CI runs the test suite on every PR.

We aim to review PRs promptly. Small, focused PRs get merged fastest.

## Reporting security issues

Please **do not** open a public issue for security vulnerabilities. Email
[narenchaudhry@gmail.com](mailto:narenchaudhry@gmail.com) instead, and we'll
work with you on a fix and disclosure timeline.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE) that covers the project.
