import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from paulias.validate import ValidationError, validate_frontmatter, validate_path, validate_target

LINK_REF_RE = re.compile(r"^\[([^\]]+)\]:\s*(.+)$")


@dataclass
class Shortlink:
    short: str
    target: str


@dataclass
class PauliasConfig:
    repo: str
    shortlinks: list[Shortlink] = field(default_factory=list)
    cname: str = ""
    branch: str = "main"
    title: str = "Paulias - static shortlinks"
    about: str = ""
    footer: str = ""


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split raw file text into (frontmatter_yaml, body). Raises ValidationError if malformed."""
    if not text.startswith("---"):
        raise ValidationError("Missing frontmatter: file must begin with ---")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValidationError("Malformed frontmatter: no closing ---")
    return parts[1], parts[2]


def _parse_frontmatter(raw_yaml: str) -> dict:
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        raise ValidationError(f"Invalid YAML in frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError("Frontmatter must be a YAML mapping")
    return data


def _parse_shortlinks(body: str) -> list[Shortlink]:
    shortlinks = []
    seen: set[str] = set()
    for line in body.splitlines():
        m = LINK_REF_RE.match(line.strip())
        if not m:
            continue
        short, target = m.group(1).strip(), m.group(2).strip()
        validate_path(short, existing=seen)
        validate_target(target)
        seen.add(short)
        shortlinks.append(Shortlink(short=short, target=target))
    return shortlinks


def load(path: Path | str, validate: bool = True) -> PauliasConfig:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"Config file not found: {path}") from exc

    raw_yaml, body = _split_frontmatter(text)
    data = _parse_frontmatter(raw_yaml)

    if validate:
        validate_frontmatter(data)

    shortlinks = _parse_shortlinks(body)

    return PauliasConfig(
        repo=str(data.get("repo", "")),
        cname=str(data.get("cname", "") or ""),
        branch=str(data.get("branch", "") or "main"),
        title=str(data.get("title", "") or "Paulias"),
        about=str(data.get("about", "") or ""),
        footer=str(data.get("footer", "") or ""),
        shortlinks=shortlinks,
    )
