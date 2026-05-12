import shutil
from pathlib import Path

from paulias.config import PauliasConfig
from paulias.render import inline_markdown, render

_BUNDLED_TEMPLATES = Path(__file__).parent / "templates"


def build(config: PauliasConfig, docs_dir: Path, local_templates: Path | None = None) -> list[Path]:
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(parents=True)

    written: list[Path] = []
    about_html = inline_markdown(config.about) if config.about else ""
    footer_html = inline_markdown(config.footer) if config.footer else ""

    if config.cname:
        p = docs_dir / "CNAME"
        p.write_text(config.cname, encoding="utf-8")
        written.append(p)

    css_dst = docs_dir / "style.css"
    css_dst.write_bytes((_BUNDLED_TEMPLATES / "style.css").read_bytes())
    written.append(css_dst)

    for link in config.shortlinks:
        link_dir = docs_dir / link.short
        link_dir.mkdir()
        p = link_dir / "index.html"
        p.write_text(render("redirect.html.j2", local_templates=local_templates, target=link.target), encoding="utf-8")
        written.append(p)

    index_path = docs_dir / "index.html"
    index_path.write_text(
        render(
            "index.html.j2",
            local_templates=local_templates,
            title=config.title,
            about=about_html,
            footer=footer_html,
            cname=config.cname,
            shortlinks=[{"short": s.short, "target": s.target} for s in config.shortlinks],
        ),
        encoding="utf-8",
    )
    written.append(index_path)

    not_found_path = docs_dir / "404.html"
    not_found_path.write_text(
        render(
            "404.html.j2",
            local_templates=local_templates,
            title=config.title,
            footer=footer_html,
        ),
        encoding="utf-8",
    )
    written.append(not_found_path)

    return written
