from pathlib import Path

import pytest

from paulias.config import PauliasConfig, Shortlink, load
from paulias.validate import ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_file_parses_all_fields():
    config = load(FIXTURES / "valid.md")
    assert isinstance(config, PauliasConfig)
    assert config.repo == "phalt/paulias-links"
    assert config.cname == "paulias.dev"
    assert config.branch == "main"
    assert config.title == "Paul's shortlinks"
    assert config.about == "A personal collection of short links."
    assert "Paul" in config.footer


def test_valid_file_parses_shortlinks():
    config = load(FIXTURES / "valid.md")
    assert len(config.shortlinks) == 3
    assert config.shortlinks[0] == Shortlink(short="gh", target="https://github.com/phalt")
    assert config.shortlinks[1].short == "drums"
    assert config.shortlinks[2] == Shortlink(short="f1", target="https://www.formula1.com")


def test_shortlink_order_is_preserved():
    config = load(FIXTURES / "valid.md")
    assert [s.short for s in config.shortlinks] == ["gh", "drums", "f1"]


def test_no_frontmatter_raises():
    with pytest.raises(ValidationError, match="Missing frontmatter"):
        load(FIXTURES / "no_frontmatter.md")


def test_invalid_yaml_raises():
    with pytest.raises(ValidationError, match="Invalid YAML"):
        load(FIXTURES / "invalid_yaml.md")


def test_no_links_loads_empty_list():
    config = load(FIXTURES / "no_links.md")
    assert config.shortlinks == []


def test_duplicate_paths_raises():
    with pytest.raises(ValidationError, match="Duplicate path"):
        load(FIXTURES / "duplicate_paths.md")


def test_missing_file_raises():
    with pytest.raises(ValidationError, match="not found"):
        load(FIXTURES / "does_not_exist.md")


def test_defaults_applied_for_optional_fields(tmp_path):
    f = tmp_path / "paulias.md"
    f.write_text("---\nrepo: phalt/links\n---\n")
    config = load(f)
    assert config.branch == "main"
    assert config.title == "Paulias"
    assert config.about == ""
    assert config.footer == ""
    assert config.cname == ""
