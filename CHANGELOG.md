# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0]

### Added

- `paulias init` — write a starter `paulias.md` with auto-detected GitHub repo.
- `paulias add <path> <url>` — append a shortlink to `paulias.md`, with `--force` and `--deploy` flags.
- `paulias delete <path>` — remove a shortlink from `paulias.md`, with `--deploy` flag.
- `paulias list` — display shortlinks as a rich table; `--json` flag for machine output.
- `paulias open <path>` — open a shortlink's target URL in the default browser; `--print` flag to output the URL instead.
- `paulias deploy` — validate, build `docs/`, commit, and push to GitHub Pages. Flags: `--dry-run`, `--no-push`, `--message`, `--force`.
- `paulias serve` — serve `docs/` locally for previewing.
- Bundled Jinja2 templates (`base.html.j2`, `index.html.j2`, `404.html.j2`, `redirect.html.j2`) and `style.css` matching the [paulblish](https://github.com/phalt/paulblish) visual theme.
- Local template override: drop a `templates/` directory next to `paulias.md` to customise any bundled template.
- Automatic commit message generation: diffs against the previous `paulias.md` to report added/removed counts.
- `CNAME` file generation when `cname` is set in frontmatter.
