from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from markdown_it import MarkdownIt

_md = MarkdownIt()
_BUNDLED = Path(__file__).parent / "templates"


def inline_markdown(text: str) -> str:
    html = _md.render(text).strip()
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return html


def _make_env(local_templates: Path | None = None) -> Environment:
    loaders: list = []
    if local_templates and local_templates.is_dir():
        loaders.append(FileSystemLoader(str(local_templates)))
    loaders.append(FileSystemLoader(str(_BUNDLED)))
    env = Environment(loader=ChoiceLoader(loaders), autoescape=True)
    env.filters["inline_markdown"] = inline_markdown
    return env


def render(template_name: str, local_templates: Path | None = None, **context: Any) -> str:
    env = _make_env(local_templates)
    return env.get_template(template_name).render(**context)
