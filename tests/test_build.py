from pathlib import Path

from paulias.build import build
from paulias.config import PauliasConfig, Shortlink

_PAULIAS_CSS_MARKER = "/* === Paulias ==="
_FIXTURES = Path(__file__).parent / "fixtures"


def _cfg(**kwargs) -> PauliasConfig:
    defaults = dict(repo="owner/repo", shortlinks=[], cname="", branch="main", title="Paulias", about="", footer="")
    defaults.update(kwargs)
    return PauliasConfig(**defaults)


def test_redirect_contains_target(tmp_path):
    cfg = _cfg(shortlinks=[Shortlink(short="gh", target="https://github.com/phalt")])
    build(cfg, tmp_path / "docs")
    html = (tmp_path / "docs" / "gh" / "index.html").read_text()
    assert "https://github.com/phalt" in html
    assert 'content="0;url=' in html
    assert "location.replace" in html


def test_redirect_has_all_fallbacks(tmp_path):
    cfg = _cfg(shortlinks=[Shortlink(short="x", target="https://example.com")])
    build(cfg, tmp_path / "docs")
    html = (tmp_path / "docs" / "x" / "index.html").read_text()
    assert "meta http-equiv" in html
    assert "<script>" in html
    assert "<a href=" in html


def test_cname_written_when_set(tmp_path):
    cfg = _cfg(cname="paulias.dev")
    build(cfg, tmp_path / "docs")
    assert (tmp_path / "docs" / "CNAME").read_text() == "paulias.dev"


def test_cname_omitted_when_not_set(tmp_path):
    cfg = _cfg(cname="")
    build(cfg, tmp_path / "docs")
    assert not (tmp_path / "docs" / "CNAME").exists()


def test_index_lists_shortlinks_in_order(tmp_path):
    cfg = _cfg(
        shortlinks=[
            Shortlink(short="gh", target="https://github.com/phalt"),
            Shortlink(short="f1", target="https://www.formula1.com"),
        ]
    )
    build(cfg, tmp_path / "docs")
    index = (tmp_path / "docs" / "index.html").read_text()
    assert index.index("gh") < index.index("f1")
    assert "/gh/" in index
    assert "https://github.com/phalt" in index
    assert "https://www.formula1.com" in index


def test_404_page_renders(tmp_path):
    cfg = _cfg()
    build(cfg, tmp_path / "docs")
    html = (tmp_path / "docs" / "404.html").read_text()
    assert "404" in html
    assert 'href="/"' in html


def test_local_template_override(tmp_path):
    local = tmp_path / "templates"
    local.mkdir()
    (local / "redirect.html.j2").write_text("CUSTOM:{{ target }}", encoding="utf-8")
    cfg = _cfg(shortlinks=[Shortlink(short="x", target="https://example.com")])
    build(cfg, tmp_path / "docs", local_templates=local)
    assert (tmp_path / "docs" / "x" / "index.html").read_text() == "CUSTOM:https://example.com"


def test_stale_files_wiped(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    stale = docs_dir / "old-link" / "index.html"
    stale.parent.mkdir()
    stale.write_text("stale", encoding="utf-8")
    build(_cfg(), docs_dir)
    assert not stale.exists()


def test_about_inline_markdown(tmp_path):
    cfg = _cfg(about="A collection of links by [Paul](https://paul.com)")
    build(cfg, tmp_path / "docs")
    index = (tmp_path / "docs" / "index.html").read_text()
    assert '<a href="https://paul.com">Paul</a>' in index


def test_footer_inline_markdown(tmp_path):
    cfg = _cfg(footer="Made by [Paul](https://paul.com) with **love**")
    build(cfg, tmp_path / "docs")
    index = (tmp_path / "docs" / "index.html").read_text()
    assert '<a href="https://paul.com">Paul</a>' in index
    assert "<strong>love</strong>" in index


def test_footer_default_attribution_when_unset(tmp_path):
    cfg = _cfg(footer="")
    build(cfg, tmp_path / "docs")
    index = (tmp_path / "docs" / "index.html").read_text()
    assert "github.com/phalt/paulias" in index


def test_style_css_matches_paulblish(tmp_path):
    build(_cfg(), tmp_path / "docs")
    bundled = (tmp_path / "docs" / "style.css").read_text(encoding="utf-8")
    marker_idx = bundled.find(_PAULIAS_CSS_MARKER)
    assert marker_idx != -1, "Paulias CSS marker not found"
    first_nl = bundled.index("\n")
    paulblish_portion = bundled[first_nl + 1 : marker_idx]
    expected = (_FIXTURES / "paulblish_style.css").read_text(encoding="utf-8")
    assert paulblish_portion == expected


def test_build_returns_written_paths(tmp_path):
    cfg = _cfg(
        cname="paulias.dev",
        shortlinks=[Shortlink(short="gh", target="https://github.com/phalt")],
    )
    written = build(cfg, tmp_path / "docs")
    paths = {p.name for p in written}
    assert "CNAME" in paths
    assert "style.css" in paths
    assert "index.html" in paths
    assert "404.html" in paths
    assert any(p.name == "index.html" and p.parent.name == "gh" for p in written)
