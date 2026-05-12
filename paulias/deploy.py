import subprocess
from pathlib import Path

from paulias.config import LINK_REF_RE, PauliasConfig


class GitError(Exception):
    pass


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        cmd = " ".join(args)
        detail = result.stderr.strip() or result.stdout.strip()
        raise GitError(f"`{cmd}` failed:\n{detail}")
    return result.stdout


def is_clean(cwd: Path) -> bool:
    out = _run(["git", "status", "--porcelain"], cwd)
    return out.strip() == ""


def stage(paths: list[Path], cwd: Path) -> None:
    _run(["git", "add", "--"] + [str(p) for p in paths], cwd)


def commit(message: str, cwd: Path) -> None:
    _run(["git", "commit", "-m", message], cwd)


def push(branch: str, cwd: Path) -> None:
    _run(["git", "push", "origin", branch], cwd)


def _parse_shorts_from_text(text: str) -> set[str]:
    return {m.group(1).strip() for line in text.splitlines() if (m := LINK_REF_RE.match(line.strip()))}


def _read_previous_paulias_md(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "show", "HEAD:paulias.md"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def generate_commit_message(cfg: PauliasConfig, cwd: Path) -> str:
    current = {s.short for s in cfg.shortlinks}
    n = len(current)

    prev_text = _read_previous_paulias_md(cwd)
    if prev_text is None:
        return f"Deploy {n} shortlink{'s' if n != 1 else ''}"

    previous = _parse_shorts_from_text(prev_text)
    added = len(current - previous)
    removed = len(previous - current)

    if added == 0 and removed == 0:
        return f"Deploy {n} shortlink{'s' if n != 1 else ''}"

    return f"Deploy {n} shortlink{'s' if n != 1 else ''} ({added} added, {removed} removed)"
