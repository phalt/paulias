import functools
import http.server
import json
import re
import subprocess
import webbrowser
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from paulias import __version__, config
from paulias import build as build_module
from paulias import deploy as deploy_module
from paulias.deploy import GitError
from paulias.validate import ValidationError, validate_path, validate_target

_console = Console()

PAULIAS_MD = "paulias.md"
LINK_REF_RE = re.compile(r"^\[([^\]]+)\]: (.+)$")

_BANNER = (
    "\b\n"
    + rf"""______           _ _
| ___ \         | (_)
| |_/ /_ _ _   _| |_  __ _ ___
|  __/ _` | | | | | |/ _` / __|
| | | (_| | |_| | | | (_| \__ \
\_|  \__,_|\__,_|_|_|\__,_|___/

Paulias. Version: {__version__}

A statically hosted URL shortener for GitHub Pages.

https://github.com/phalt/paulias"""
)

STARTER_TEMPLATE = """\
---
repo: {repo}
cname:
# branch: main
title: My shortlinks
about:
footer:
---

"""


def _find_paulias_md() -> Path:
    path = Path(PAULIAS_MD)
    if not path.exists():
        raise click.ClickException(f"{PAULIAS_MD} not found in current directory")
    return path


def _add_link_ref(text: str, short: str, url: str, force: bool = False) -> str:
    lines = text.splitlines(keepends=True)
    existing_idx = None
    last_ref_idx = None

    for i, line in enumerate(lines):
        m = LINK_REF_RE.match(line.rstrip("\n\r"))
        if m:
            if m.group(1) == short:
                existing_idx = i
            last_ref_idx = i

    new_line = f"[{short}]: {url}\n"

    if existing_idx is not None and force:
        lines[existing_idx] = new_line
    elif last_ref_idx is not None:
        lines.insert(last_ref_idx + 1, new_line)
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(new_line)

    return "".join(lines)


def _delete_link_ref(text: str, short: str) -> tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    new_lines = []
    found = False
    for line in lines:
        m = LINK_REF_RE.match(line.rstrip("\n\r"))
        if m and m.group(1) == short:
            found = True
            continue
        new_lines.append(line)
    return "".join(new_lines), found


def _existing_shorts(text: str) -> set[str]:
    return {m.group(1) for line in text.splitlines() if (m := LINK_REF_RE.match(line.strip()))}


def _detect_github_repo() -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        url = result.stdout.strip().removesuffix(".git")
        if "github.com" not in url:
            return None
        if url.startswith("git@github.com:"):
            return url[len("git@github.com:") :]
        if "github.com/" in url:
            return url.split("github.com/", 1)[1] or None
    except Exception:
        return None
    return None


@click.group(invoke_without_command=True, help=_BANNER)
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("list")
@click.option("--json", "as_json", is_flag=True, help="Print as JSON.")
def list_cmd(as_json: bool) -> None:
    """Print current shortlinks."""
    path = _find_paulias_md()
    try:
        cfg = config.load(path)
    except ValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps([{"short": s.short, "target": s.target} for s in cfg.shortlinks], indent=2))
        return

    domain = cfg.cname or cfg.repo
    count = len(cfg.shortlinks)
    noun = "entry" if count == 1 else "entries"
    _console.print(f"\n[bold]{cfg.title}[/bold]  ({count} {noun}, deploying to {domain})\n")

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 4, 0, 0))
    table.add_column("short")
    table.add_column("target")
    for s in cfg.shortlinks:
        table.add_row(s.short, s.target)
    _console.print(table)
    _console.print()


@main.command("add")
@click.argument("path")
@click.argument("url")
@click.option("--force", is_flag=True, help="Overwrite an existing entry with the same path.")
@click.option("--deploy", "run_deploy", is_flag=True, help="Run 'paulias deploy' after adding.")
def add_cmd(path: str, url: str, force: bool, run_deploy: bool) -> None:
    """Add a shortlink to paulias.md."""
    paulias_path = _find_paulias_md()

    try:
        validate_path(path)
        validate_target(url)
    except ValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    text = paulias_path.read_text(encoding="utf-8")
    if path in _existing_shorts(text) and not force:
        raise click.ClickException(f"Path {path!r} already exists. Use --force to overwrite.")

    new_text = _add_link_ref(text, path, url, force=force)
    paulias_path.write_text(new_text, encoding="utf-8")
    _console.print(f"[green]✓[/green] Added [{path}]: {url}")
    _console.print("  Run [bold]paulias deploy[/bold] to publish.", style="dim")

    if run_deploy:
        ctx = click.get_current_context()
        ctx.invoke(deploy_cmd)


@main.command("delete")
@click.argument("path")
@click.option("--deploy", "run_deploy", is_flag=True, help="Run 'paulias deploy' after deleting.")
def delete_cmd(path: str, run_deploy: bool) -> None:
    """Remove a shortlink from paulias.md."""
    paulias_path = _find_paulias_md()
    text = paulias_path.read_text(encoding="utf-8")
    new_text, found = _delete_link_ref(text, path)
    if not found:
        raise click.ClickException(f"Path {path!r} not found in {PAULIAS_MD}.")
    paulias_path.write_text(new_text, encoding="utf-8")
    _console.print(f"[green]✓[/green] Deleted [{path}].")
    _console.print("  Run [bold]paulias deploy[/bold] to publish.", style="dim")

    if run_deploy:
        ctx = click.get_current_context()
        ctx.invoke(deploy_cmd)


@main.command("init")
@click.option("--force", is_flag=True, help="Overwrite an existing paulias.md.")
@click.option("--repo", "repo_override", default=None, help="Set repo field explicitly.")
def init_cmd(force: bool, repo_override: str | None) -> None:
    """Write a starter paulias.md to the current directory."""
    paulias_path = Path(PAULIAS_MD)
    if paulias_path.exists() and not force:
        raise click.ClickException(f"{PAULIAS_MD} already exists. Use --force to overwrite.")

    repo = repo_override or _detect_github_repo() or "<owner>/<repo>"
    paulias_path.write_text(STARTER_TEMPLATE.format(repo=repo), encoding="utf-8")
    _console.print(f"[green]✓[/green] Wrote {PAULIAS_MD}.")
    _console.print("\nNext steps:", style="bold")
    _console.print("  1. Edit paulias.md and fill in your details.")
    _console.print("  2. Run [bold]paulias add <path> <url>[/bold] to add shortlinks.")
    _console.print("  3. Run [bold]paulias deploy[/bold] to build and publish.")


@main.command("deploy")
@click.option("--dry-run", is_flag=True, help="Build but do not commit or push.")
@click.option("--no-push", is_flag=True, help="Commit but do not push.")
@click.option("--message", "-m", default=None, help="Override the generated commit message.")
@click.option("--force", is_flag=True, help="Skip validation.")
def deploy_cmd(dry_run: bool, no_push: bool, message: str | None, force: bool) -> None:
    """Build and deploy to GitHub Pages."""
    paulias_path = _find_paulias_md()
    try:
        cfg = config.load(paulias_path, validate=not force)
    except ValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    docs_dir = paulias_path.parent / "docs"
    local_templates = paulias_path.parent / "templates"
    written = build_module.build(cfg, docs_dir, local_templates if local_templates.is_dir() else None)
    n = len(cfg.shortlinks)
    noun = "shortlink" if n == 1 else "shortlinks"

    if dry_run:
        _console.print(f"[green]✓[/green] Built {len(written)} files — dry run complete.")
        return

    repo_root = paulias_path.parent

    if deploy_module.is_clean(repo_root):
        _console.print("[green]✓[/green] Nothing to commit — already up to date.")
        return

    try:
        deploy_module.stage([paulias_path, docs_dir], repo_root)
        msg = message or deploy_module.generate_commit_message(cfg, repo_root)
        deploy_module.commit(msg, repo_root)
    except GitError as exc:
        raise click.ClickException(str(exc)) from exc

    if no_push:
        _console.print(f"[green]✓[/green] Committed: [italic]{msg}[/italic] (not pushed)")
        return

    try:
        deploy_module.push(cfg.branch, repo_root)
    except GitError as exc:
        raise click.ClickException(str(exc)) from exc

    domain = cfg.cname or cfg.repo
    _console.print(f"[green]✓[/green] Deployed {n} {noun} → [bold]{domain}[/bold]")


@main.command("open")
@click.argument("path")
@click.option("--print", "print_only", is_flag=True, help="Print the target URL instead of opening it.")
def open_cmd(path: str, print_only: bool) -> None:
    """Open a shortlink's target URL in the default browser."""
    paulias_path = _find_paulias_md()
    try:
        cfg = config.load(paulias_path)
    except ValidationError as exc:
        raise click.ClickException(str(exc)) from exc

    match = next((s for s in cfg.shortlinks if s.short == path), None)
    if match is None:
        raise click.ClickException(f"Path {path!r} not found in {PAULIAS_MD}.")

    if print_only:
        click.echo(match.target)
    else:
        webbrowser.open(match.target)
        _console.print(f"[green]✓[/green] Opening {match.target}")


@main.command("serve")
@click.option("--port", default=8000, show_default=True, help="Port to listen on.")
def serve_cmd(port: int) -> None:
    """Serve docs/ locally for previewing."""
    paulias_path = _find_paulias_md()
    docs_dir = (paulias_path.parent / "docs").resolve()
    if not docs_dir.is_dir():
        raise click.ClickException(f"{docs_dir} not found — run 'paulias deploy --dry-run' first.")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(docs_dir))
    with http.server.HTTPServer(("", port), handler) as httpd:
        click.echo(f"Serving {docs_dir} at http://localhost:{port}/ (Ctrl+C to stop)")
        httpd.serve_forever()
