# AGENTS.md — shopify-theme-builder

> Cross-agent entry point (the [agents.md](https://agents.md) convention, read
> automatically by OpenAI Codex, Cursor, Zed, Gemini CLI, and others). If you are
> a coding agent asked to **build, generate, scaffold, or design a Shopify theme**,
> follow the instructions here. They mirror `SKILL.md` (the native format for
> Claude Code / Claude apps) — both describe the same workflow.

You build **production-grade, Online Store 2.0 (OS 2.0) Shopify themes** that a
non-technical merchant can run entirely from the theme editor, that pass
`shopify theme check` with zero errors, and that meet Shopify Theme Store
requirements. Do not generate the whole theme in one pass — move through the
gated phases below and checkpoint with the user.

## Read these when the relevant phase needs them (progressive disclosure)

- `SKILL.md` — the full workflow, phase gates, and token vocabulary (start here).
- `references/shopify-standards.md` — official standards + Theme Store rules.
- `references/settings-control.md` — the "100% theme-editor controllable" rulebook.
- `references/os2-architecture.md` — JSON templates, sections, blocks, section groups.
- `references/design-tokens.md` — settings_schema ↔ CSS custom properties.
- `references/liquid-patterns.md`, `references/i18n-rtl.md`,
  `references/accessibility.md`, `references/performance.md`,
  `references/seo-structured-data.md` — the quality references.
- `references/interview.md` — the Phase 0 question bank.
- `references/qa-checklist.md` — the Phase 6 pass/fail checklist.
- `assets/theme-skeleton/` — the scaffold base to copy.
- `examples/section-hero.liquid` — the reference section every new section copies.

## Three hard constraints (never trade these away)

1. **Shopify-compliant** — correct layout/filenames, valid `{% schema %}` on
   every section, `theme-check` clean, no deprecated Liquid, no private APIs.
   When unsure, do exactly what the official docs and **Dawn** do.
2. **100% theme-editor controllable** — no hard-coded text, color, font, image
   URL, or layout choice anywhere; every such value is a setting, block, or
   section group. If a merchant would ever need a developer to change something
   cosmetic or structural, the section is not done.
3. **Systemized** — one token layer (`settings_schema.json` → CSS custom
   properties in `snippets/css-variables.liquid`) drives all color, type,
   spacing, radius, shadow, motion. Sections read `var(--token)` only.

## Phase gates (do not cross a gate until its exit condition is met)

0. **Discovery interview (blocking)** — do not write code first. Interview the
   user in batched groups (`references/interview.md`), infer and state defaults
   for anything skipped, offer a "you decide" escape hatch. If the user says
   "just build it," collapse into stated assumptions.
1. **Architecture plan (approval gate)** — template→JSON map, section inventory,
   block breakdown, design-token schema, metafield map, file tree. Wait for
   approval.
2. **Scaffold** — copy `assets/theme-skeleton/`; wire tokens, layout, section
   groups, and locales.
3. **Build sections** — header/footer → home → product → collection/search →
   cart → content/blog → utility. Each ships complete: Liquid + `{% schema %}` +
   token-driven scoped CSS + any web-component JS + locale keys. Pattern-match
   `examples/section-hero.liquid`.
4. **Design pass** — enforce type scale, spacing rhythm, contrast, motion, states.
5. **i18n & RTL pass** — every string a translation key; layouts mirror in RTL.
6. **QA & validation** — `shopify theme check` (zero errors),
   `python scripts/validate_theme.py <theme-dir>`, and the
   `references/qa-checklist.md` audit (incl. "no code required by merchant").
7. **Package & hand off** — confirm the theme zips clean; write `THEME_NOTES.md`.

## Conventions

Sections/snippets `kebab-case.liquid`; JSON templates `templates/<type>.json`;
section groups `sections/header-group.json` / `footer-group.json`; vanilla JS
only (`type="module"`, custom elements, event delegation, no jQuery, no globals);
DRY Liquid; responsive images (`image_url` + `srcset` + `width`/`height` +
`loading="lazy"`); every shopper-facing string is a `{{ 'key' | t }}` translation
key; every setting has a `label`, sits under a `header`, and has `info` where
non-obvious. Logical CSS properties everywhere so RTL mirrors for free.

## Composition

This skill composes `everything-claude-code:orchestrate` (phased workflow) and
`ui-ux-pro-max` (design system) when they are available in the environment. If
they are not (e.g. you are Codex or Cursor), apply the phases and design rigor
described here directly — the workflow is self-contained.
