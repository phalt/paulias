import pytest

from paulias.validate import ValidationError, validate_frontmatter, validate_path, validate_target

# validate_path


def test_valid_path():
    validate_path("gh")
    validate_path("my-link")
    validate_path("link_1")
    validate_path("a1b2c3")


def test_path_uppercase_raises():
    with pytest.raises(ValidationError, match="Invalid path"):
        validate_path("GH")


def test_path_with_space_raises():
    with pytest.raises(ValidationError, match="Invalid path"):
        validate_path("my link")


def test_path_starts_with_hyphen_raises():
    with pytest.raises(ValidationError, match="Invalid path"):
        validate_path("-gh")


def test_path_too_long_raises():
    with pytest.raises(ValidationError, match="Invalid path"):
        validate_path("a" * 65)


def test_path_exactly_64_chars():
    validate_path("a" * 64)


RESERVED = ["cname", "404", "index", "style", "docs", "assets", "static", "templates", "paulias"]


@pytest.mark.parametrize("reserved", RESERVED)
def test_reserved_paths_raise(reserved):
    with pytest.raises(ValidationError, match="reserved"):
        validate_path(reserved)


def test_duplicate_path_raises():
    with pytest.raises(ValidationError, match="Duplicate path"):
        validate_path("gh", existing={"gh"})


def test_no_existing_set_allows_any_path():
    validate_path("gh", existing=None)


# validate_target


def test_valid_https_target():
    validate_target("https://github.com/phalt")


def test_valid_http_target():
    validate_target("http://example.com")


def test_target_no_scheme_raises():
    with pytest.raises(ValidationError, match="scheme must be http or https"):
        validate_target("github.com/phalt")


def test_target_ftp_scheme_raises():
    with pytest.raises(ValidationError, match="scheme must be http or https"):
        validate_target("ftp://example.com")


def test_target_no_host_raises():
    with pytest.raises(ValidationError, match="missing host"):
        validate_target("https://")


# validate_frontmatter


def test_valid_frontmatter():
    validate_frontmatter({"repo": "phalt/paulias-links"})


def test_frontmatter_missing_repo_raises():
    with pytest.raises(ValidationError, match="Missing required frontmatter field: repo"):
        validate_frontmatter({})


def test_frontmatter_invalid_repo_format_raises():
    with pytest.raises(ValidationError, match="Invalid repo"):
        validate_frontmatter({"repo": "justname"})


def test_frontmatter_valid_cname():
    validate_frontmatter({"repo": "phalt/links", "cname": "paulias.dev"})


def test_frontmatter_cname_with_scheme_raises():
    with pytest.raises(ValidationError, match="Invalid cname"):
        validate_frontmatter({"repo": "phalt/links", "cname": "https://paulias.dev"})


def test_frontmatter_cname_with_path_raises():
    with pytest.raises(ValidationError, match="Invalid cname"):
        validate_frontmatter({"repo": "phalt/links", "cname": "paulias.dev/path"})


def test_frontmatter_empty_branch_raises():
    with pytest.raises(ValidationError, match="Invalid branch"):
        validate_frontmatter({"repo": "phalt/links", "branch": ""})


def test_frontmatter_valid_branch():
    validate_frontmatter({"repo": "phalt/links", "branch": "gh-pages"})
