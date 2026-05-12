# Paulias

A statically hosted URL shortener. Paulias takes a markdown file of short paths and target URLs, generates a directory of HTML redirect files, and pushes them to a GitHub Pages repo. No server, no JavaScript required, no database.

## What is this?

Paulias turns a single human-readable markdown file into a fully working URL shortener hosted for free on GitHub Pages. You manage shortlinks by editing `paulias.md`; Paulias builds and deploys the static HTML.

- **File over app.** The list of shortlinks lives in a single markdown file with YAML frontmatter and link references. Edit it anywhere — GitHub, your phone, Obsidian, or the CLI.
- **No server.** Each shortlink is a tiny static HTML file containing a meta refresh redirect. GitHub Pages serves it for free.
- **The config is the source of truth.** The generated HTML is derived; the markdown file is what matters.

## Quick start

```sh
# install
uv tool install paulias

# create a new shortener repo
gh repo create your-username/my-links --public --clone
cd my-links

# initialise
paulias init

# add some links
paulias add gh https://github.com/your-username
paulias add blog https://yourblog.com

# build and publish
paulias deploy
```

Your shortlinks are now live at `https://your-username.github.io/my-links/gh`, etc.

## Installation

```sh
uv tool install paulias
```

Requires Python 3.14+. After install, run `paulias` from inside any directory containing a `paulias.md` file.

## Commands

### `paulias init`

Write a starter `paulias.md` to the current working directory.

```sh
paulias init
```

Auto-detects the `repo` field from `git remote get-url origin` if the cwd is a git repo pointing at GitHub. Errors if `paulias.md` already exists unless `--force` is passed.

| Flag | Description |
|------|-------------|
| `--force` | Overwrite an existing `paulias.md`. |
| `--repo` | Set the `repo` field explicitly instead of auto-detecting. |

### `paulias add`

Append a new shortlink to `paulias.md`.

```sh
paulias add <path> <url>
```

Validates the path and URL before writing. Errors if `<path>` already exists. Does not build or push.

| Flag | Description |
|------|-------------|
| `--force` | Overwrite an existing entry with the same path. |
| `--deploy` | Run `paulias deploy` immediately after adding. |

### `paulias delete`

Remove a shortlink from `paulias.md`.

```sh
paulias delete <path>
```

Errors if `<path>` does not exist. Does not build or push.

| Flag | Description |
|------|-------------|
| `--deploy` | Run `paulias deploy` immediately after deleting. |

### `paulias list`

Print the current shortlinks as a formatted table.

```sh
paulias list
```

Reads only from `paulias.md` — does not look at `docs/`.

| Flag | Description |
|------|-------------|
| `--json` | Print as JSON instead of a table. |

### `paulias open`

Open a shortlink's target URL in the default browser.

```sh
paulias open <path>
```

Looks up `<path>` in `paulias.md` and opens its target URL directly — useful for quick verification without typing the full domain.

| Flag | Description |
|------|-------------|
| `--print` | Print the target URL to stdout instead of opening it. |

### `paulias deploy`

Build the site and push to GitHub Pages.

```sh
paulias deploy
```

In order: validate `paulias.md` → wipe and regenerate `docs/` → stage files → commit → push. The commit message is generated automatically: `Deploy N shortlinks (M added, K removed)`.

`deploy` is idempotent — running it twice with no changes produces no commit.

| Flag | Description |
|------|-------------|
| `--dry-run` | Build to `docs/` but do not commit or push. |
| `--no-push` | Commit but do not push. |
| `--message`, `-m` | Override the generated commit message. |
| `--force` | Skip the validation step (not recommended). |

## `paulias.md` format

The config lives at `paulias.md` in the root of your shortener repo.

```markdown
---
cname: paulias.dev
repo: your-username/my-links
branch: main
title: "My shortlinks"
about: "A personal collection of short links."
footer: "Made by [You](https://yoursite.com) with [Paulias](https://github.com/phalt/paulias)."
---

[gh]: https://github.com/your-username
[blog]: https://yourblog.com
```

Shortlinks are standard markdown link reference definitions. Each line maps a short path to its target URL. The order of entries is preserved on disk so the file diffs cleanly.

### Frontmatter fields

| Field | Required | Description |
|-------|----------|-------------|
| `repo` | yes | GitHub repo in `owner/name` form. Used by `deploy`. |
| `cname` | no | Custom domain. Writes a `CNAME` file to `docs/CNAME`. |
| `branch` | no | Branch to push to. Default `main`. |
| `title` | no | Title shown on the index page. Default `Paulias`. |
| `about` | no | Short description shown on the index page. |
| `footer` | no | Footer text. Supports inline markdown for links and emphasis. |

### Path rules

- Lowercase alphanumerics, hyphens, and underscores only.
- Must start with an alphanumeric character.
- Maximum 64 characters.
- Must not collide with reserved paths: `CNAME`, `404`, `index`, `style`, `docs`, `assets`, `static`, `templates`, `paulias`.

## Custom domain setup

Set `cname` in your frontmatter to your custom domain:

```yaml
cname: links.yourdomain.com
```

`paulias deploy` will write a `CNAME` file to `docs/CNAME`. Then in your DNS provider, add a `CNAME` record pointing `links.yourdomain.com` to `your-username.github.io`.

Finally, in your GitHub repo settings under **Pages**, set the custom domain.

## Deployment workflow

```sh
# initialise once
paulias init

# daily usage
paulias add gh https://github.com/your-username
paulias add f1 https://www.formula1.com
paulias deploy

# editing by hand also works
vim paulias.md
paulias deploy
```

`paulias add` and `paulias delete` only edit `paulias.md`. Use `paulias deploy` to build and ship. This separation lets you batch edits, edit the config by hand, and review the diff before publishing.

## Template customisation

Create a `templates/` directory next to `paulias.md` to override any bundled template:

```
my-links/
├── paulias.md
└── templates/
    ├── base.html.j2
    ├── index.html.j2
    └── 404.html.j2
```

Local templates take precedence over the bundled defaults. Available Jinja2 context variables:

| Variable | Type | Description |
|----------|------|-------------|
| `title` | str | Site title from frontmatter. |
| `about` | str | About text from frontmatter. |
| `footer` | str | Footer HTML, already rendered from markdown. |
| `cname` | str | Custom domain or empty string. |
| `shortlinks` | list | List of `{"short": ..., "target": ...}`. |

## Development

```sh
git clone https://github.com/phalt/paulias
cd paulias
make install   # uv sync
make test      # pytest
make lint      # ruff check
make format    # ruff format
```

## Fork your own copy

Paulias is designed to be self-hosted on GitHub Pages with zero running costs. To set up your own shortener:

1. Create a new public GitHub repo (e.g. `your-username/my-links`).
2. In repo **Settings → Pages**, set source to the `main` branch, folder `/docs`.
3. Install Paulias: `uv tool install paulias`.
4. Clone your repo, run `paulias init`, add links, and `paulias deploy`.

## License

MIT — see [LICENSE](LICENSE).
