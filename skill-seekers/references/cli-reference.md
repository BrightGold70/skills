# Skill Seekers CLI Reference

Condensed reference for CLI commands and options. For full docs see the [official README](https://github.com/yusufkaraaslan/Skill_Seekers) and [skillseekersweb.com](https://skillseekersweb.com/).

## Installation profiles

| Install | Scope |
|--------|--------|
| `pip install skill-seekers` | CLI only: scrape, github, pdf, package |
| `pip install skill-seekers[mcp]` | + MCP server (Claude Code, Cursor, Windsurf) |
| `pip install skill-seekers[gemini]` | + Google Gemini packaging/upload |
| `pip install skill-seekers[openai]` | + OpenAI ChatGPT packaging/upload |
| `pip install skill-seekers[all-llms]` | + Gemini and OpenAI |
| `pip install skill-seekers[all]` | All features |

Alternative: `uv tool install skill-seekers`

## Scrape (documentation)

```bash
skill-seekers scrape --config <path_or_name>   # preset name or path to JSON
skill-seekers scrape --url <base_url> --name <skill_name> [--description "..."]
skill-seekers scrape --config configs/react.json --async --workers 8   # faster
skill-seekers scrape --config configs/godot.json --skip-scrape          # reuse existing data
```

## GitHub

```bash
skill-seekers github --repo owner/repo
skill-seekers github --repo owner/repo --profile <name>   # use config profile
skill-seekers github --repo owner/repo --non-interactive  # CI: no prompts
skill-seekers github --repo owner/repo --include-issues --max-issues 100 --include-changelog --include-releases
```

Env: `GITHUB_TOKEN` for higher rate limits. Config: `skill-seekers config --github`.

## PDF

```bash
skill-seekers pdf --pdf <path> --name <skill_name>
skill-seekers pdf --pdf <path> --name <name> --extract-tables --parallel --workers 8
skill-seekers pdf --pdf <path> --name <name> --ocr          # scanned PDFs
skill-seekers pdf --pdf <path> --name <name> --password <pwd>   # encrypted
```

## Unified (multi-source + conflict detection)

```bash
skill-seekers unified --config configs/react_unified.json
```

Config JSON: `sources` array with `type`: `documentation` | `github` | `pdf`; optional `merge_mode`, `rule-based` or AI.

## Enhance and package

```bash
skill-seekers enhance <output_dir>              # e.g. output/react/
skill-seekers package <output_dir>             # default: Claude ZIP
skill-seekers package <output_dir> --target gemini
skill-seekers package <output_dir> --target openai
skill-seekers package <output_dir> --target markdown
```

## Upload and install

```bash
skill-seekers upload <path.zip>                 # needs ANTHROPIC_API_KEY
skill-seekers install --config react            # full pipeline, optional upload
skill-seekers install --config react --no-upload
skill-seekers install-agent <output_dir> --agent cursor
skill-seekers install-agent <output_dir> --agent all
```

Supported agents: `cursor`, `claude`, `windsurf`, `amp`, `goose`, `opencode`, `letta`, `aide`, `neovate`, etc.

## Config and resume

```bash
skill-seekers config --github
skill-seekers config --show
skill-seekers config --test
skill-seekers resume --list
skill-seekers resume <job_id>
```

## Platform comparison (--target)

| Platform   | Format           | Upload | Enhancement |
|-----------|-------------------|--------|-------------|
| claude    | ZIP + YAML        | API    | Yes         |
| gemini    | tar.gz            | API    | Yes         |
| openai    | ZIP + Vector Store| API    | Yes         |
| markdown  | ZIP               | Manual | No          |

## Environment variables

- `ANTHROPIC_API_KEY` – Claude API (enhance/upload)
- `ANTHROPIC_BASE_URL` – Custom Claude-compatible endpoint
- `GITHUB_TOKEN` – GitHub API (higher limits, private repos)
- `GOOGLE_API_KEY` – Gemini
- `OPENAI_API_KEY` – OpenAI

## Preset config names (examples)

`react`, `django`, `vue`, `fastapi`, `godot`, `ansible-core`. Unified: `react_unified`, `django_unified`, `fastapi_unified`.
