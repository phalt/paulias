# Contributing

## Development setup

```sh
git clone https://github.com/phalt/paulias
cd paulias
make install   # uv sync — installs all dependencies
```

Requires Python 3.14+. The `.python-version` file pins the version; `uv` reads it automatically.

## Common commands

```sh
make install   # uv sync
make test      # uv run pytest
make lint      # uv run ruff check .
make format    # uv run ruff format .
make clean     # remove __pycache__, dist, .ruff_cache
```

## Rules

- **Every change must include tests.** No code gets merged without coverage. Write tests first if it helps.
- No comments unless the *why* is non-obvious. No docstrings beyond a one-liner.
- `ValidationError` is the only error type raised by `config.py` and `validate.py`. Surface it to the user via `click.ClickException`.
- Git operations shell out to the system `git` binary via `subprocess` — no GitPython.
- Follow the flat package layout: `paulias/` at the repo root, no `src/`.

## Project structure

See [`SPEC.md`](SPEC.md) for the full specification and implementation plan, and [`CLAUDE.md`](CLAUDE.md) for AI-assistant-specific conventions.

## Submitting a PR

1. Fork the repo and create a branch.
2. Make your changes with tests.
3. Run `make lint` and `make test` — both must pass.
4. Open a PR against `main`. The CI workflow runs lint and tests automatically.
