# CLAUDE.md

## Project overview

Paulias (`paulias`) is a CLI tool that takes a markdown file of short paths and target URLs, generates a directory of static HTML redirect files, and pushes them to a GitHub Pages repo. See `SPEC.md` for the full specification.

## Implementation progress

Current phase: **Phase 3 — Build pipeline**

After completing each phase step, check it off in `SPEC.md` (change `- [ ]` to `- [x]`) and update the current phase note above when the phase changes.

## Project conventions

- **Package layout:** Flat layout with `paulias/` at repo root (no `src/`).
- **Dependency management:** `uv` for everything. `uv.lock` committed. `.python-version` pins Python to 3.14.
- **Build backend:** `hatchling` in `pyproject.toml`.
- **Linting/formatting:** `ruff` configured in `pyproject.toml`. Line length 120, target `py314`, rules `E F I UP B SIM`.
- **Tests:** `pytest` in `tests/` at repo root. Fixtures in `tests/fixtures/`. Use `tmp_path` for filesystem tests.
- **Makefile:** `make install`, `make test`, `make lint`, `make format`, `make clean`.

## Key rules

- **Every implementation change must include tests.** Before marking a phase step done, either confirm existing coverage is sufficient or write new tests. No untested code gets checked off.
- **No comments** unless the why is non-obvious. No docstrings beyond a one-liner when needed.
- Imports at file top only. Never inline imports.
- `ValidationError` is the single error type raised by `config.py` and `validate.py` — surface it to the user with a clear message and non-zero exit.
- Shortlinks are stored as markdown link references (`[short]: https://target`). The parser uses `^\[([^\]]+)\]: (.+)$`.
- Reserved paths use lowercase: `cname`, `404`, `index`, `style`, `docs`, `assets`, `static`, `templates`, `paulias`.
- Git operations shell out to the system `git` binary via `subprocess` — no GitPython.

## Development commands

```sh
make install        # uv sync
make test           # uv run pytest
make lint           # uv run ruff check .
make format         # uv run ruff format .
make clean          # remove __pycache__, dist, etc.
```

## Architecture

Key modules:

- `cli.py` — Click entry point, subcommands
- `config.py` — `PauliasConfig` + `Shortlink` dataclasses, `load()` parser
- `validate.py` — path, target URL, and frontmatter validators; `ValidationError`
- `build.py` — `docs/` generator (phase 3)
- `deploy.py` — git commit + push wrapper (phase 4)
- `render.py` — Jinja2 environment + template resolution (phase 3)
- `paulias/templates/` — bundled Jinja2 templates and `style.css`
