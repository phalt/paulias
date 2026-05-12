import re
from urllib.parse import urlparse

RESERVED_PATHS = frozenset({"cname", "404", "index", "style", "docs", "assets", "static", "templates", "paulias"})
PATH_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")


class ValidationError(Exception):
    pass


def validate_path(short: str, existing: set[str] | None = None) -> None:
    if not PATH_RE.match(short):
        raise ValidationError(
            f"Invalid path {short!r}: must match ^[a-z0-9][a-z0-9_-]{{0,63}}$ "
            "(lowercase alphanumerics, hyphens, underscores; start with alphanumeric; max 64 chars)"
        )
    if short in RESERVED_PATHS:
        raise ValidationError(f"Invalid path {short!r}: reserved name")
    if existing is not None and short in existing:
        raise ValidationError(f"Duplicate path {short!r}")


def validate_target(target: str) -> None:
    try:
        parsed = urlparse(target)
    except Exception as exc:
        raise ValidationError(f"Invalid target URL {target!r}") from exc
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"Invalid target URL {target!r}: scheme must be http or https")
    if not parsed.netloc:
        raise ValidationError(f"Invalid target URL {target!r}: missing host")


def validate_frontmatter(data: dict) -> None:
    repo = data.get("repo")
    if not repo:
        raise ValidationError("Missing required frontmatter field: repo")
    if not REPO_RE.match(str(repo)):
        raise ValidationError(f"Invalid repo {repo!r}: must be in owner/name form")

    cname = data.get("cname")
    if cname:
        cname = str(cname)
        if "/" in cname or ":" in cname:
            raise ValidationError(f"Invalid cname {cname!r}: must be a hostname with no scheme or path")

    branch = data.get("branch")
    if branch is not None and not str(branch).strip():
        raise ValidationError("Invalid branch: must be a non-empty string")
