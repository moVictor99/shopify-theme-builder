---
name: shopify-theme-builder
description: >-
  Build a complete, clean, Online Store 2.0 Shopify theme from a guided
  requirements interview. Use when a user wants to build, generate, scaffold,
  or design a Shopify theme, Shopify sections, JSON templates, Liquid, section
  groups, or a fully theme-editor-controllable storefront (including bilingual
  / RTL Arabic stores). Produces a zip-ready theme that passes theme-check and
  meets Shopify Theme Store requirements.
license: MIT
---

# Shopify Theme Builder

You build **production-grade, Online Store 2.0 (OS 2.0) Shopify themes** that a
non-technical merchant can run entirely from the theme editor. Everything you
emit must satisfy Shopify's official theme-development standards and Theme Store
review requirements, and must look designed — never templated.

You compose two skills:

- **`everything-claude-code:orchestrate`** — structure the build as gated,
  verifiable phases with explicit hand-offs. Do not generate the whole theme in
  one pass; move phase by phase and checkpoint with the user.
- **`ui-ux-pro-max`** — the aesthetic backbone: type scale, spacing rhythm,
  color tokens, hierarchy, motion, states, accessibility. Invoke it during
  Phase 1 (design direction) and Phase 4 (design pass).

**Reconciliation rule:** when `orchestrate` or `ui-ux-pro-max` conventions
conflict with anything here, prefer *their* conventions and note the swap in the
theme's `THEME_NOTES.md`. When *Shopify's* documented conventions conflict with
any of the three, Shopify wins — always.

---

## The three hard constraints (never trade these away)

1. **Shopify-compliant.** Correct directory layout and file names, valid
   `{% schema %}` on every section, all required templates/config present,
   `theme-check` clean (zero errors), no deprecated Liquid, no private APIs.
   When unsure, do exactly what the official docs and **Dawn** do. See
   `references/shopify-standards.md`.
2. **100% theme-editor controllable — zero code for the merchant.** No
   hard-coded text, color, font, image URL, or layout choice anywhere. Every
   such value is wired to a setting, block, or section-group. If a merchant
   would ever need a developer to change something cosmetic or structural, the
   section is **not done**. See `references/settings-control.md`.
3. **Systemized, not hand-sprayed.** One token layer
   (`settings_schema.json` → CSS custom properties) drives all color, type,
   spacing, radius, shadow, motion. Changing a token restyles the whole theme.
   See `references/design-tokens.md`.

Supporting bars, each with a reference: OS 2.0 architecture
(`references/os2-architecture.md`), DRY Liquid (`references/liquid-patterns.md`),
performance / Core Web Vitals (`references/performance.md`), accessibility
WCAG 2.1 AA (`references/accessibility.md`), i18n + RTL
(`references/i18n-rtl.md`), SEO + structured data
(`references/seo-structured-data.md`).

**Progressive disclosure:** keep this file in context; open a reference only
when its phase needs it. Don't preload all of `references/`.

---

## Phase gates (from `orchestrate`)

Move through these in order. Each phase has an exit condition; do not cross a
gate until it's met. If the user says "just build it," collapse Phases 0–1 into
stated assumptions and proceed — but still produce the plan text.

### Phase 0 — Discovery interview *(blocking)*
Do **not** write code first. Interview the user in batched, easy groups, infer
defaults for anything skipped (and state them), and always offer a "you decide"
escape hatch. Skip questions already answered earlier in the conversation.
Cover: **strategy** (store archetype, primary action, vertical/product type);
**brand & design** (aesthetic, reference brands, existing assets, token
preferences); **language & market** (locales, RTL/Arabic, currency/format);
**scope** (which templates/pages, custom landings); **features & sections**
(merchandising, trust/social proof, content, marketing app blocks); **data
model** (metafields and how they surface); **constraints** (perf target, a11y
level, browser support, deadlines, app deps). Use the `AskUserQuestion` tool for
the batched groups. Full question bank: `references/interview.md`.
**Exit:** you can state the store archetype, locale/RTL decision, template list,
section inventory, and token direction.

### Phase 1 — Architecture plan *(approval gate)*
Write a plan the user approves: template→JSON map, section inventory (mark
reusable ones), block breakdown, the design-token schema, the metafield map,
and the full file tree. Invoke `ui-ux-pro-max` here to lock the design system.
**Exit:** user approves (or said "just build it").

### Phase 2 — Scaffold
Copy `assets/theme-skeleton/` as the base. Wire `settings_schema.json` (tokens),
`layout/theme.liquid`, the CSS token bridge (`assets/base.css`), section groups
(`header-group.json`, `footer-group.json`), and `en.default.json` +
`en.default.schema.json`. Every template is a JSON template.
**Exit:** valid empty theme that would load in a store.

### Phase 3 — Build sections *(iterative, one coherent group at a time)*
Order: header/footer group → homepage sections → product → collection/search →
cart/drawer → content/blog → utility templates (search, 404, password,
customer/account). Each section ships **complete**: Liquid + `{% schema %}` +
scoped styles (token-driven) + any JS (web-component pattern) + locale keys.
Pattern-match every section against `examples/section-hero.liquid`.
**Exit:** all in-scope sections built and self-consistent.

### Phase 4 — Design-system pass
Apply `ui-ux-pro-max`: enforce type scale, spacing rhythm, contrast, motion, and
interaction states. Remove anything that reads as default Shopify/Dawn.
**Exit:** the theme looks intentionally designed.

### Phase 5 — i18n & RTL pass
Confirm every visible string is a `{{ 't:...' }}` key, locale files are
complete, and layouts mirror correctly in RTL (logical CSS, `dir`, mirrored
components). See `references/i18n-rtl.md`.
**Exit:** RTL preview is correct; no hard-coded UI copy.

### Phase 6 — QA & validation
Run/describe `shopify theme check` (**zero errors**), validate every JSON
template and schema, and audit Theme-Store-level compliance. Explicitly walk
every section and confirm **no hard-coded copy, color, or image** remains — a
merchant could reproduce the intended design from the customizer alone. Check
a11y (keyboard, contrast, ARIA) and performance (image `srcset`, script defer,
CLS). Emit the checklist from `references/qa-checklist.md`, which must include
the line items **"No code required by merchant"** and **"Shopify standards
compliant."** `scripts/validate_theme.py` sanity-checks JSON/schemas.
**Exit:** checklist all-pass.

### Phase 7 — Package & hand off
Confirm the theme zips clean (correct root layout, no stray files), then write
`THEME_NOTES.md` (tokens, section inventory, how-to-customize) into the theme
and give the user setup + upload notes.
**Exit:** zip-ready theme + notes delivered.

---

## Token vocabulary (use these exact names everywhere)

Follow Dawn's **color-scheme groups** for color, layered with a systematic
scale for the rest. Sections expose a `color_scheme` setting; global tokens live
in `settings_schema.json` and are emitted as CSS custom properties in
`snippets/css-variables.liquid` (loaded from `layout/theme.liquid`).

- **Color** (per scheme, RGB-triplet vars, Dawn-style):
  `--color-background`, `--color-foreground`, `--color-surface`,
  `--color-border`, `--color-primary`, `--color-on-primary`,
  `--color-secondary`, `--color-accent`, `--color-sale`, `--color-focus`.
- **Type:** `--font-heading-family`, `--font-body-family`, fluid scale
  `--font-h1 … --font-h6`, `--font-body`, `--font-small`; weights
  `--font-heading-weight`, `--font-body-weight`; `--line-heading`, `--line-body`.
- **Space:** `--page-width`, `--section-padding-block`, `--grid-gap`, and an
  8-pt-based scale `--space-1 … --space-12`.
- **Radius:** `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-pill`.
- **Shadow:** `--shadow-sm`, `--shadow-md`, `--shadow-lg`.
- **Motion:** `--ease`, `--duration-fast`, `--duration-base`, `--duration-slow`;
  always guard with `@media (prefers-reduced-motion: reduce)`.

Every section's scoped CSS reads these vars — never literal values. Full mapping
in `references/design-tokens.md`.

---

## Conventions you always follow

- **Naming:** sections `kebab-case.liquid`; snippets `kebab-case.liquid`;
  section-group JSON `header-group.json` / `footer-group.json`; JSON templates
  `templates/<type>.json` and named variants `templates/<type>.<name>.json`.
- **CSS:** one `assets/base.css` for tokens/reset/utilities; per-section styles
  scoped via a unique section wrapper class or `{{ section.id }}`, injected with
  a `{% stylesheet %}` tag or a scoped `<style>` — no global bleed, no `!important`.
- **JS:** vanilla only, `type="module"`, custom-elements / web-components for
  interactivity, event delegation, no globals, progressive enhancement (works
  without JS where possible). No jQuery.
- **Liquid:** DRY — anything used twice becomes a snippet. Responsive images via
  `image_url` + `srcset` + `width`/`height` + `loading="lazy"`. Never a
  deprecated object/filter/tag.
- **Every string** rendered to a shopper is a translation key; every setting has
  a clear `label`, is grouped under a `header`, and has `info` where non-obvious.

Bundled resources (open by relative path when the phase calls for them):
`references/*.md`, `assets/theme-skeleton/` (scaffold base), `examples/`
(pattern targets), `scripts/validate_theme.py`.
