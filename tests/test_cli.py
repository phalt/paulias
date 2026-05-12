import json

import pytest
from click.testing import CliRunner

from paulias.cli import _add_link_ref, _delete_link_ref, main

runner = CliRunner()

VALID_MD = """\
---
repo: phalt/paulias-links
cname: paulias.dev
title: Test links
---

[gh]: https://github.com/phalt
[f1]: https://www.formula1.com
"""


# --- _add_link_ref unit tests ---


def test_add_link_ref_appends_after_last_entry():
    result = _add_link_ref(VALID_MD, "blog", "https://paulwrites.software")
    lines = [ln for ln in result.splitlines() if ln.startswith("[")]
    assert lines == [
        "[gh]: https://github.com/phalt",
        "[f1]: https://www.formula1.com",
        "[blog]: https://paulwrites.software",
    ]


def test_add_link_ref_force_replaces_in_place():
    result = _add_link_ref(VALID_MD, "gh", "https://github.com/new", force=True)
    lines = [ln for ln in result.splitlines() if ln.startswith("[")]
    assert lines[0] == "[gh]: https://github.com/new"
    assert "[gh]: https://github.com/phalt" not in result


def test_add_link_ref_force_preserves_position():
    result = _add_link_ref(VALID_MD, "gh", "https://github.com/new", force=True)
    lines = [ln for ln in result.splitlines() if ln.startswith("[")]
    assert lines == [
        "[gh]: https://github.com/new",
        "[f1]: https://www.formula1.com",
    ]


def test_add_link_ref_no_existing_refs():
    text = "---\nrepo: phalt/links\n---\n\n"
    result = _add_link_ref(text, "gh", "https://github.com/phalt")
    assert "[gh]: https://github.com/phalt" in result


def test_add_link_ref_preserves_frontmatter():
    result = _add_link_ref(VALID_MD, "blog", "https://example.com")
    assert "repo: phalt/paulias-links" in result
    assert "cname: paulias.dev" in result


# --- _delete_link_ref unit tests ---


def test_delete_link_ref_removes_correct_line():
    result, found = _delete_link_ref(VALID_MD, "gh")
    assert found
    assert "[gh]: https://github.com/phalt" not in result
    assert "[f1]: https://www.formula1.com" in result


def test_delete_link_ref_preserves_frontmatter():
    result, _ = _delete_link_ref(VALID_MD, "gh")
    assert "repo: phalt/paulias-links" in result


def test_delete_link_ref_not_found_returns_false():
    _, found = _delete_link_ref(VALID_MD, "nonexistent")
    assert not found


def test_delete_link_ref_not_found_text_unchanged():
    original = VALID_MD
    result, _ = _delete_link_ref(original, "nonexistent")
    assert result == original


# --- fixtures ---


@pytest.fixture
def paulias_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "paulias.md").write_text(VALID_MD)
    return tmp_path


# --- paulias list ---


def test_list_shows_all_shortlinks(paulias_dir):
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "gh" in result.output
    assert "https://github.com/phalt" in result.output
    assert "f1" in result.output
    assert "https://www.formula1.com" in result.output


def test_list_shows_title_and_count(paulias_dir):
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "Test links" in result.output
    assert "2 entries" in result.output


def test_list_json_structure(paulias_dir):
    result = runner.invoke(main, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0] == {"short": "gh", "target": "https://github.com/phalt"}
    assert data[1] == {"short": "f1", "target": "https://www.formula1.com"}


def test_list_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["list"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_list_single_entry_uses_singular(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "paulias.md").write_text("---\nrepo: phalt/links\ntitle: Mine\n---\n\n[gh]: https://github.com/phalt\n")
    result = runner.invoke(main, ["list"])
    assert "1 entry" in result.output


# --- paulias add ---


def test_add_writes_link_ref_to_file(paulias_dir):
    result = runner.invoke(main, ["add", "blog", "https://paulwrites.software"])
    assert result.exit_code == 0
    text = (paulias_dir / "paulias.md").read_text()
    assert "[blog]: https://paulwrites.software" in text


def test_add_preserves_existing_order(paulias_dir):
    runner.invoke(main, ["add", "blog", "https://paulwrites.software"])
    lines = [ln for ln in (paulias_dir / "paulias.md").read_text().splitlines() if ln.startswith("[")]
    assert lines == [
        "[gh]: https://github.com/phalt",
        "[f1]: https://www.formula1.com",
        "[blog]: https://paulwrites.software",
    ]


def test_add_duplicate_errors_without_force(paulias_dir):
    result = runner.invoke(main, ["add", "gh", "https://github.com/new"])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_add_force_replaces_existing(paulias_dir):
    result = runner.invoke(main, ["add", "--force", "gh", "https://github.com/new"])
    assert result.exit_code == 0
    text = (paulias_dir / "paulias.md").read_text()
    assert "[gh]: https://github.com/new" in text
    assert "[gh]: https://github.com/phalt" not in text


def test_add_force_preserves_position(paulias_dir):
    runner.invoke(main, ["add", "--force", "gh", "https://github.com/new"])
    lines = [ln for ln in (paulias_dir / "paulias.md").read_text().splitlines() if ln.startswith("[")]
    assert lines[0] == "[gh]: https://github.com/new"
    assert lines[1] == "[f1]: https://www.formula1.com"


def test_add_invalid_path_errors(paulias_dir):
    result = runner.invoke(main, ["add", "INVALID", "https://example.com"])
    assert result.exit_code != 0
    assert "Invalid path" in result.output


def test_add_invalid_url_errors(paulias_dir):
    result = runner.invoke(main, ["add", "blog", "not-a-url"])
    assert result.exit_code != 0


def test_add_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["add", "gh", "https://github.com/phalt"])
    assert result.exit_code != 0
    assert "not found" in result.output


# --- paulias delete ---


def test_delete_removes_correct_entry(paulias_dir):
    result = runner.invoke(main, ["delete", "gh"])
    assert result.exit_code == 0
    text = (paulias_dir / "paulias.md").read_text()
    assert "[gh]: https://github.com/phalt" not in text


def test_delete_preserves_other_entries(paulias_dir):
    runner.invoke(main, ["delete", "gh"])
    text = (paulias_dir / "paulias.md").read_text()
    assert "[f1]: https://www.formula1.com" in text


def test_delete_missing_path_errors(paulias_dir):
    result = runner.invoke(main, ["delete", "nonexistent"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_delete_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["delete", "gh"])
    assert result.exit_code != 0


# --- paulias init ---


def test_init_writes_paulias_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--repo", "phalt/my-links"])
    assert result.exit_code == 0
    assert (tmp_path / "paulias.md").exists()


def test_init_repo_flag_sets_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--repo", "owner/mylinks"])
    text = (tmp_path / "paulias.md").read_text()
    assert "repo: owner/mylinks" in text


def test_init_already_exists_errors(paulias_dir):
    result = runner.invoke(main, ["init"])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_init_force_overwrites(paulias_dir):
    result = runner.invoke(main, ["init", "--force", "--repo", "phalt/new"])
    assert result.exit_code == 0
    text = (paulias_dir / "paulias.md").read_text()
    assert "repo: phalt/new" in text


def test_init_placeholder_when_no_remote(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("paulias.cli._detect_github_repo", lambda: None)
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0
    text = (tmp_path / "paulias.md").read_text()
    assert "<owner>/<repo>" in text


def test_init_auto_detects_github_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("paulias.cli._detect_github_repo", lambda: "phalt/paulias")
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0
    text = (tmp_path / "paulias.md").read_text()
    assert "repo: phalt/paulias" in text


def test_init_repo_flag_overrides_auto_detect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("paulias.cli._detect_github_repo", lambda: "phalt/paulias")
    runner.invoke(main, ["init", "--repo", "other/repo"])
    text = (tmp_path / "paulias.md").read_text()
    assert "repo: other/repo" in text
    assert "phalt/paulias" not in text


def test_serve_errors_without_docs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "paulias.md").write_text(VALID_MD, encoding="utf-8")
    result = runner.invoke(main, ["serve"])
    assert result.exit_code != 0
    assert "deploy" in result.output.lower()


def test_serve_starts_server(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "paulias.md").write_text(VALID_MD, encoding="utf-8")
    (tmp_path / "docs").mkdir()

    started = {}

    class FakeServer:
        def __init__(self, addr, handler):
            started["addr"] = addr
            started["dir"] = handler.keywords["directory"]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def serve_forever(self):
            raise KeyboardInterrupt

    monkeypatch.setattr("paulias.cli.http.server.HTTPServer", FakeServer)
    result = runner.invoke(main, ["serve", "--port", "9876"])
    assert started["addr"] == ("", 9876)
    assert started["dir"] == str(tmp_path / "docs")
    assert "9876" in result.output
