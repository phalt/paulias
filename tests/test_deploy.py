from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from paulias.cli import main
from paulias.config import PauliasConfig, Shortlink
from paulias.deploy import GitError, commit, generate_commit_message, is_clean, push, stage


def _cfg(**kwargs) -> PauliasConfig:
    defaults = dict(repo="owner/repo", shortlinks=[], cname="", branch="main", title="Paulias", about="", footer="")
    defaults.update(kwargs)
    return PauliasConfig(**defaults)


def _ok(stdout=""):
    m = MagicMock()
    m.returncode = 0
    m.stdout = stdout
    m.stderr = ""
    return m


def _fail(stderr="error", stdout=""):
    m = MagicMock()
    m.returncode = 1
    m.stdout = stdout
    m.stderr = stderr
    return m


# --- unit tests for deploy.py functions ---


def test_is_clean_true(tmp_path):
    with patch("subprocess.run", return_value=_ok("")) as mock_run:
        assert is_clean(tmp_path) is True
    mock_run.assert_called_once_with(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=tmp_path
    )


def test_is_clean_false(tmp_path):
    with patch("subprocess.run", return_value=_ok(" M paulias.md\n")):
        assert is_clean(tmp_path) is False


def test_stage_calls_git_add(tmp_path):
    paths = [Path("/repo/paulias.md"), Path("/repo/docs")]
    with patch("subprocess.run", return_value=_ok()) as mock_run:
        stage(paths, tmp_path)
    mock_run.assert_called_once_with(
        ["git", "add", "--", "/repo/paulias.md", "/repo/docs"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )


def test_commit_calls_git_commit(tmp_path):
    with patch("subprocess.run", return_value=_ok()) as mock_run:
        commit("Deploy 3 shortlinks", tmp_path)
    mock_run.assert_called_once_with(
        ["git", "commit", "-m", "Deploy 3 shortlinks"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )


def test_push_calls_git_push(tmp_path):
    with patch("subprocess.run", return_value=_ok()) as mock_run:
        push("main", tmp_path)
    mock_run.assert_called_once_with(
        ["git", "push", "origin", "main"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )


def test_git_error_surfaced(tmp_path):
    with patch("subprocess.run", return_value=_fail("fatal: not a git repository")), pytest.raises(
        GitError, match="fatal: not a git repository"
    ):
        is_clean(tmp_path)


# --- generate_commit_message ---

PREV_PAULIAS_MD = """\
---
repo: owner/repo
---

[gh]: https://github.com/phalt
[f1]: https://www.formula1.com
"""


def test_commit_message_no_prior_commit(tmp_path):
    cfg = _cfg(shortlinks=[Shortlink("gh", "https://github.com/phalt")])
    with patch("subprocess.run", return_value=_fail("fatal: ambiguous argument 'HEAD'")):
        msg = generate_commit_message(cfg, tmp_path)
    assert msg == "Deploy 1 shortlink"


def test_commit_message_no_changes(tmp_path):
    cfg = _cfg(shortlinks=[Shortlink("gh", "https://github.com/phalt"), Shortlink("f1", "https://www.formula1.com")])
    with patch("subprocess.run", return_value=_ok(PREV_PAULIAS_MD)):
        msg = generate_commit_message(cfg, tmp_path)
    assert msg == "Deploy 2 shortlinks"


def test_commit_message_added_and_removed(tmp_path):
    cfg = _cfg(
        shortlinks=[
            Shortlink("gh", "https://github.com/phalt"),
            Shortlink("drums", "https://alesis.com"),
        ]
    )
    with patch("subprocess.run", return_value=_ok(PREV_PAULIAS_MD)):
        msg = generate_commit_message(cfg, tmp_path)
    # f1 removed, drums added
    assert msg == "Deploy 2 shortlinks (1 added, 1 removed)"


def test_commit_message_only_added(tmp_path):
    cfg = _cfg(
        shortlinks=[
            Shortlink("gh", "https://github.com/phalt"),
            Shortlink("f1", "https://www.formula1.com"),
            Shortlink("drums", "https://alesis.com"),
        ]
    )
    with patch("subprocess.run", return_value=_ok(PREV_PAULIAS_MD)):
        msg = generate_commit_message(cfg, tmp_path)
    assert msg == "Deploy 3 shortlinks (1 added, 0 removed)"


# --- CLI integration tests (mock subprocess) ---

VALID_PAULIAS_MD = """\
---
repo: owner/repo
cname:
branch: main
title: Test
about:
footer:
---

[gh]: https://github.com/phalt
"""


def _write_paulias_md(d: Path, content: str = VALID_PAULIAS_MD) -> None:
    (d / "paulias.md").write_text(content, encoding="utf-8")


def test_deploy_dry_run_no_git(tmp_path, monkeypatch):
    _write_paulias_md(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(main, ["deploy", "--dry-run"])
        git_calls = [c for c in mock_run.call_args_list if c.args and "git" in str(c.args[0])]
        assert git_calls == [], "dry-run must not call git"
    assert "Dry run" in result.output


def test_deploy_no_push_commits_but_not_pushes(tmp_path, monkeypatch):
    _write_paulias_md(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    def fake_run(args, **kwargs):
        if "status" in args:
            return _ok(" M paulias.md\n")
        if "show" in args:
            return _fail("fatal: no HEAD")
        if "add" in args:
            return _ok()
        if "commit" in args:
            return _ok()
        return _ok()

    with patch("subprocess.run", side_effect=fake_run) as mock_run:
        runner.invoke(main, ["deploy", "--no-push"])

    commands = [c.args[0] for c in mock_run.call_args_list]
    assert any("commit" in str(c) for c in commands), "should have called git commit"
    assert not any("push" in str(c) for c in commands), "should NOT have called git push"


def test_deploy_idempotent_clean_tree(tmp_path, monkeypatch):
    _write_paulias_md(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    with patch("paulias.deploy.is_clean", return_value=True):
        result = runner.invoke(main, ["deploy"])

    assert "Nothing to commit" in result.output
    assert result.exit_code == 0


def test_deploy_custom_message(tmp_path, monkeypatch):
    _write_paulias_md(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    committed_messages = []

    def fake_run(args, **kwargs):
        if "status" in args:
            return _ok(" M paulias.md\n")
        if "show" in args:
            return _fail("no HEAD")
        if "add" in args:
            return _ok()
        if "commit" in args:
            committed_messages.append(args[args.index("-m") + 1])
            return _ok()
        if "push" in args:
            return _ok()
        return _ok()

    with patch("subprocess.run", side_effect=fake_run):
        runner.invoke(main, ["deploy", "--no-push", "-m", "my custom message"])

    assert committed_messages == ["my custom message"]
