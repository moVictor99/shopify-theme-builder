# shopify-theme-builder

<p>
  <a href="https://github.com/moVictor99/shopify-theme-builder/stargazers"><img src="https://img.shields.io/github/stars/moVictor99/shopify-theme-builder?style=flat&color=8a6d3b" alt="Stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/moVictor99/shopify-theme-builder?color=informational" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Online%20Store-2.0-96BF48?logo=shopify&logoColor=white" alt="Online Store 2.0">
  <img src="https://img.shields.io/badge/works%20with-Claude%20·%20Codex%20·%20Cursor%20·%20Windsurf-5A45FF" alt="Agents">
  <a href="https://github.com/moVictor99/shopify-theme-builder/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs welcome"></a>
</p>

> An [Anthropic Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
> that turns Claude into a senior Shopify theme engineer. It interviews you about
> your store, then generates a **complete, clean, Online Store 2.0 theme** that a
> non-technical merchant can run entirely from the theme editor — zip-ready,
> `theme-check`-clean, and built to Shopify Theme Store standards.

<!-- screenshots placeholder: add editor + storefront captures here -->

## What it does

- **Interviews first, builds second.** A batched, adaptive discovery interview
  captures your strategy, brand, languages/markets, template scope, features,
  metafields, and constraints — then infers strong defaults for anything you
  skip and states its assumptions.
- **Generates a real OS 2.0 theme.** JSON templates, modular sections with
  `{% schema %}`, reusable blocks and app-block slots, header/footer section
  groups, and metafield-driven content — no legacy `.liquid` templates where a
  JSON template belongs.
- **Everything is editable in the customizer.** No hard-coded text, colors,
  fonts, or image URLs. Every section supports add/remove/reorder blocks, ships
  sensible defaults, and exposes clearly labeled, grouped, `info`-annotated
  settings. If a merchant would ever need to touch code to rebrand or
  repopulate, that's treated as a defect.
- **Systemized design.** One token layer (`settings_schema.json` → CSS custom
  properties) drives color, type, spacing, radius, shadow, and motion. Change a
  token, restyle the whole store.
- **Bilingual & RTL by default.** Locale files with all UI strings translated,
  logical CSS, `dir` handling, and mirrored layouts — Arabic/English works out
  of the box.
- **Fast, accessible, SEO-sound.** Responsive `srcset` images, deferred module
  scripts, Core-Web-Vitals-aware markup (LCP < 2.5s, CLS < 0.1), WCAG 2.1 AA,
  and structured data (Product, BreadcrumbList, Organization).

## Requirements

- Claude Code (or any Claude client that loads Agent Skills).
- These companion skills present in the environment, which this skill composes:
  - `everything-claude-code:orchestrate` (phased multi-agent workflow)
  - `ui-ux-pro-max` (design-system rigor)
- Optional for validation: [Shopify CLI](https://shopify.dev/docs/api/shopify-cli)
  (`shopify theme check`) and Python 3 (for `scripts/validate_theme.py`).

## Install

This skill is **agent-agnostic**. The instructions are plain Markdown
(`SKILL.md` / `AGENTS.md`) plus a theme scaffold, so any coding agent can use
them — each just consumes them through its own mechanism. There is no universal
package installer for agent skills; the table below is the "install" step for
each tool.

| Agent | How to install |
|-------|----------------|
| **Claude Code / Claude apps** | Native skill. Run `./install.sh` (macOS/Linux) or `./install.ps1` (Windows), **or** copy the folder into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project). Restart, then ask *"build a Shopify theme."* |
| **OpenAI Codex** | Reads `AGENTS.md` automatically. Just have this repo in your project (or copy `AGENTS.md` + `references/` + `assets/` + `examples/` into it). |
| **Cursor** | Ships a `.cursor/rules/shopify-theme-builder.mdc` adapter that activates on theme tasks. Cursor also reads `AGENTS.md`. Keep the repo in your workspace. |
| **Windsurf** | Ships a `.windsurf/rules/shopify-theme-builder.md` adapter. Keep the repo in your workspace. |
| **Aider / Gemini CLI / other** | Point the agent at `AGENTS.md` (e.g. Aider: `aider --read AGENTS.md`; Gemini CLI: reference it as context). The workflow is self-contained. |

**Claude quick install:**

```bash
# from inside the cloned repo
./install.sh            # user-level (all projects)
./install.sh --project  # current project only
# Windows:  ./install.ps1   (add -Project for project-level)
```

Verify by asking your agent to *"build a Shopify theme"* — it should start the
Phase 0 discovery interview.

> Why not "one installer for everything"? `SKILL.md`'s auto-discovery format is
> Anthropic-specific; Codex/Cursor/Windsurf use their own rules files. This repo
> ships adapters for each so the **same** workflow (`SKILL.md` ↔ `AGENTS.md`)
> drives all of them.

## Usage

Just describe what you want and let the interview run:

```
You:    Build me a Shopify theme for a bilingual (Arabic/English) cosmetics
        brand. Luxury, minimal, conversion-focused.

Claude: (activates shopify-theme-builder → Phase 0)
        A few quick groups so I build the right thing:
        1) Store archetype — high-conversion DTC, editorial, catalog-heavy,
           single-product landing, subscription, or hybrid?
        2) Homepage's single most important action?
        3) RTL confirmed for Arabic, and is English the default locale?
        ...
        (you answer, or say "you decide" — Claude states defaults)

Claude: Phase 1 — here's the architecture plan: templates → JSON map,
        section inventory, design tokens, metafield map, file tree. Approve?

You:    Approved.

Claude: Phase 2 scaffold → Phase 3 sections → … → Phase 7 packages a
        zip-ready theme + THEME_NOTES.md.
```

Prefer to skip the questions? Say **"just build it"** and Claude collapses the
interview into stated assumptions and proceeds.

## What you get

A theme directory with the standard OS 2.0 layout:

```
theme/
├── assets/      config/      layout/
├── locales/     sections/    snippets/     templates/
└── THEME_NOTES.md   # tokens, section inventory, how to customize
```

Zip the theme folder and upload it under **Online Store → Themes → Add theme →
Upload zip file**, or push it with the Shopify CLI.

## Customization

Everything is driven from the theme editor:

- **Rebrand** — Theme settings → Colors / Typography / Layout tokens.
- **Populate & rearrange** — add/remove/reorder sections and blocks per template.
- **Languages** — Theme settings → language switcher; edit copy under the theme's
  locale editor. RTL turns on automatically for RTL locales.

Developers extending the skill can pattern-match new sections against
[`examples/section-hero.liquid`](examples/section-hero.liquid) and follow the
docs in [`references/`](references/).

## How it's structured

| Path | Purpose |
|------|---------|
| `SKILL.md` | Workflow, phase gates, hard constraints, token vocabulary (Claude-native format) |
| `AGENTS.md` | Same workflow as a cross-agent entry point (Codex, Cursor, Gemini CLI, …) |
| `.cursor/`, `.windsurf/` | Thin per-agent rule adapters pointing back to `SKILL.md` |
| `install.sh` / `install.ps1` | One-command install into a Claude skills directory |
| `references/` | Deep guides loaded on demand (standards, settings-control, OS 2.0, tokens, i18n/RTL, a11y, perf, SEO, interview, QA) |
| `assets/theme-skeleton/` | Minimal valid OS 2.0 theme used as the scaffold base |
| `examples/` | Reference-quality section + template + settings to pattern-match |
| `scripts/validate_theme.py` | Sanity-checks JSON templates and schema validity |

## License

MIT.
