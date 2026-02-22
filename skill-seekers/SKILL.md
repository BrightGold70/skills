---
name: skill-seekers
description: Use when converting documentation websites, GitHub repositories, or PDFs into Claude/Cursor skills; when scraping, analyzing, packaging, or uploading skills; or when configuring MCP or multi-source conflict detection for skill generation.
---

# Skill Seekers

Automated tool that transforms documentation websites, GitHub repositories, and PDF files into production-ready Claude/Cursor skills. Use this skill when the user needs to create, scrape, enhance, package, or upload skills from docs, code, or PDFs.

## When to Use This Skill

Trigger when the user:
- Wants to turn a documentation site, GitHub repo, or PDF into a Claude/Cursor skill
- Asks to scrape docs, analyze a repo, or extract content from PDFs for skills
- Needs to package, enhance, or upload an existing skill
- Wants MCP integration, preset configs, or conflict detection between docs and code
- Mentions Skill Seekers, skill-seekers, or "doc to skill" workflows

## Tool Overview

Skill Seekers:
1. **Scrapes** docs, GitHub repos, and PDFs
2. **Analyzes** code (AST parsing for Python, JS, TS, Java, C++, Go)
3. **Detects** conflicts between documentation and implementation
4. **Organizes** content into categorized references
5. **Enhances** with AI (optional) and **packages** to ZIP (or platform-specific format)

Result: production-ready skills in ~20–40 minutes instead of manual summarization.

## Installation

```bash
# CLI only (recommended minimum)
pip install skill-seekers
# or with uv
uv tool install skill-seekers

# With MCP (Claude Code, Cursor, Windsurf)
pip install skill-seekers[mcp]

# Multi-LLM (Gemini, OpenAI)
pip install skill-seekers[all-llms]

# Everything
pip install skill-seekers[all]
```

Setup wizard: `skill-seekers-setup`

## Core Commands

| Command | Purpose |
|--------|--------|
| `skill-seekers scrape --config <config>` | Scrape documentation site (use preset or local JSON config) |
| `skill-seekers scrape --url <url> --name <name>` | Quick scrape without config file |
| `skill-seekers github --repo owner/repo` | Scrape GitHub repo (code + metadata, optional issues/changelog) |
| `skill-seekers pdf --pdf <path> --name <name>` | Extract content from PDF (optional: `--ocr`, `--extract-tables`, `--parallel`) |
| `skill-seekers unified --config <config>` | Multi-source: docs + GitHub + PDF with conflict detection |
| `skill-seekers enhance <output_dir>` | AI-enhance SKILL.md (API or local agent) |
| `skill-seekers package <output_dir>` | Package skill to .zip (default Claude; use `--target gemini|openai|markdown` for other platforms) |
| `skill-seekers upload <path.zip>` | Upload to Claude (requires `ANTHROPIC_API_KEY`) |
| `skill-seekers install --config <name>` | One-shot: fetch config → scrape → enhance → package → optional upload |
| `skill-seekers config --github` | Configure GitHub token / profiles (rate limits, multi-account) |
| `skill-seekers install-agent <output_dir> --agent cursor` | Install built skill to Cursor (`~/.cursor/skills/` when `--agent cursor`) |

Detailed CLI options and platform comparison: see **references/cli-reference.md**.

## Presets and Configs

Presets (by name): `react`, `django`, `vue`, `fastapi`, `godot`, `ansible-core`, etc. Fetch from API or use local JSON in `configs/`.

```bash
skill-seekers scrape --config configs/react.json
skill-seekers install --config react --no-upload
```

Unified configs (docs + GitHub): e.g. `configs/react_unified.json`, `configs/django_unified.json`.

## Cursor / Claude Integration

- **Install to Cursor**: After packaging, run  
  `skill-seekers install-agent output/<name>/ --agent cursor`  
  to copy the skill into `~/.cursor/skills/` (or use this project’s `/install-skills` if the skill lives under `skills/`).
- **MCP**: Install with `pip install skill-seekers[mcp]` and configure the MCP server (stdio or HTTP) for your agent; then use natural language to scrape, package, and manage configs.
- **Custom Claude-compatible API**: Set `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY` for enhancement/upload to non-Anthropic endpoints (e.g. GLM-4.7).

## Rate Limits and Profiles

For GitHub scraping, configure tokens to avoid rate limits:

```bash
skill-seekers config --github
skill-seekers github --repo owner/repo --profile work   # use named profile
skill-seekers github --repo owner/repo --non-interactive  # CI: fail fast, no prompts
```

Config: `~/.config/skill-seekers/config.json`. Strategies: `prompt`, `wait`, `switch`, `fail`.

## Resume and Large Runs

- Resume interrupted jobs: `skill-seekers resume --list` then `skill-seekers resume <job_id>`.
- Async scraping (faster): `skill-seekers scrape --config configs/godot.json --async --workers 8`.
- Large docs: use `skill-seekers estimate <config>` first; consider splitting configs and router/hub skills (see official docs).

## References

- **Repository**: [github.com/yusufkaraaslan/Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers)
- **Presets and docs**: [skillseekersweb.com](https://skillseekersweb.com/)
- **CLI and platform details**: [references/cli-reference.md](references/cli-reference.md)
