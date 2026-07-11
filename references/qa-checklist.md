# Phase 6 — QA & Validation Checklist

Emit this as an explicit **pass/fail** report before hand-off. Every item has a short "how to verify". Nothing ships until this is green. See [shopify-standards.md](./shopify-standards.md) and [settings-control.md](./settings-control.md).

**Always run these two first (read exit codes — never pipe through `tail`/`head`, it masks failures):**
- `python scripts/validate_theme.py .` → must pass (structural + **import/sync landmine** lint).
- `shopify theme check` → must report **0 errors** (drive warnings to 0 too).

---

## 0. Reliability & sync *(theme-check does NOT catch these — see [reliability-and-sync.md](./reliability-and-sync.md))*

These are the #1 cause of "it validated but the build is broken." All must pass.

- [ ] **No `{% stylesheet %}` / `{% javascript %}` tags** — `grep -rnE '\{%-?\s*(stylesheet|javascript)\s*-?%\}' sections snippets` is empty. Scoped CSS uses `{% style %}`; JS is external `assets/*.js`.
- [ ] **All section block names ≤ 25 chars** — longer names silently drop the section + its template (→ 404).
- [ ] **Color-scheme `role` keys all valid** — no `shadow`/invented keys; the editor registers the schemes (fonts are not serif fallback).
- [ ] **Header/footer/cart via section groups** — no static `{% section %}` in `layout/*.liquid` (`grep -rnE "\{%-?\s*section\s+'" layout` empty).
- [ ] **No filter piped inside an `image_tag` arg** (e.g. `alt: x | escape`) — pre-computed instead.
- [ ] **Single-variant add-to-cart works** — a 1-variant product still POSTs a variant `id`; add-to-cart and Buy-it-now succeed (no "Required parameter missing: items").
- [ ] **Every custom element has `display: block`** in CSS — no collapsed/ignored padding on `<cart-drawer>`, recs, predictive search, etc.
- [ ] **No mobile horizontal overflow** — sliders/galleries/embeds don't scroll the page sideways at 390px (`min-inline-size: 0` on grid/flex children; `overflow-x: clip` on scrollers).
- [ ] **RTL positioning correct** — no `translateX`-based centering that fails to mirror; carousels use rect-based deltas.
- [ ] **Re-render-safe third-party widgets** — SDKs injected via `createElement`, re-init on `variant:change` / section load (not a declarative `<script src>` in re-rendered HTML).
- [ ] **No cruft in theme root** — no `npm-cache/`, `node_modules/`, `.DS_Store`, `*.log`, `.shopify/`, nested `*.zip`; root has only the standard theme dirs.

## A. Shopify compliance

- [ ] **Required files/dirs present** — verify §1/§2 of shopify-standards; all JSON templates + `customers/*` exist.
- [ ] **theme-check: 0 errors** — run `shopify theme check`; read the summary line.
- [ ] **No deprecated Liquid** — grep for `include `, `img_url`; must be `render`, `image_url`.
- [ ] **Layout objects present** — `content_for_header` + `content_for_layout` in `theme.liquid` & `password.liquid`.
- [ ] **Section groups** — header/footer via `sections/*-group.json`, not static sections.
- [ ] **Every section has schema + presets + `@app`** — open each in the editor "Add section" list.
- [ ] **No console errors / 404s** — load home, product, collection, cart, search, 404, blog, article; check devtools console + network.

## B. Settings control (zero merchant code)

- [ ] **No code required by merchant** — every string/image/link/color/font/spacing is editor-editable (run §6 audit in settings-control).
- [ ] **Shopify standards compliant** — settings use correct input types; `t:` keys resolve.
- [ ] **Blocks used for repeated content** — `{{ block.shopify_attributes }}` on each; `{{ section.shopify_attributes }}` on section.
- [ ] **Sensible defaults / presets** — add a fresh section; it renders complete and attractive.
- [ ] **Show/hide + layout controls** — toggles and selects behave as labeled.
- [ ] **Grouping + info** — settings organized under `header`s; non-obvious ones have `info`.

## C. OS 2.0 architecture

- [ ] **JSON templates everywhere** (except `gift_card.liquid`) — verify `templates/*.json`.
- [ ] **Sections are self-contained & reorderable** — drag/reorder/remove in editor without breakage.
- [ ] **App blocks / app embeds work** — insert a test app block; confirm app embed injects via `content_for_header`.

## D. Liquid quality

- [ ] **DRY** — shared markup extracted to snippets via `render`; no copy-paste loops.
- [ ] **No unused assigns/snippets** — theme-check `UnusedAssign`/`UnusedSnippet` clean.
- [ ] **Pagination** — collection/blog/search lists wrapped in `paginate`.
- [ ] **Escaping** — user/merchant strings use `| escape`; URLs safe.

## E. Design system / tokens

- [ ] **Single token layer** — colors/type/space/radius/shadow/motion driven by the shared `--*` custom properties; no literal hex/px scattered in sections.
- [ ] **Color schemes** — sections reference `color_scheme`; foreground/background pairs meet contrast.
- [ ] **Fluid type scale** — headings use `--font-h1..h6`, body `--font-body`.
- [ ] **8pt spacing** — spacing pulls from `--space-*` / range→token vars.

## F. Accessibility

- [ ] **Keyboard** — all interactive elements reachable & operable by Tab/Enter/Esc; menus, sliders, modals trap/return focus.
- [ ] **Contrast** — text vs background ≥ WCAG AA (4.5:1 body, 3:1 large); check each color scheme.
- [ ] **ARIA & semantics** — correct roles/labels; landmarks (`main`, `nav`), `alt` on images, `aria-expanded` on toggles.
- [ ] **Focus states** — visible focus ring using `--color-focus`; never `outline:none` without replacement.
- [ ] **Skip link** — "skip to content" targets `#MainContent`.
- [ ] **Reduced motion** — animations guarded by `@media (prefers-reduced-motion: reduce)`.

## G. Performance

- [ ] **Image srcset** — every `<img>` has `srcset` + `sizes` (verify markup).
- [ ] **width/height** — every `<img>` has intrinsic `width`+`height` (or `aspect-ratio`) → no CLS.
- [ ] **Lazy loading** — offscreen images `loading="lazy"`; LCP image `eager` + `fetchpriority="high"`.
- [ ] **Script defer** — all `<script src>` `defer`/`type="module"`; no parser-blocking JS.
- [ ] **CLS** — Lighthouse CLS ≈ 0; reserve space for media/embeds.
- [ ] **LCP target** — Lighthouse LCP good (< ~2.5s lab) on home, product, collection.
- [ ] **Asset budgets** — theme-check `AssetSizeCSS/JS` clean.

## H. i18n & RTL

- [ ] **Every string translated** — no literal shopper-facing text; keys resolve in `en.default.json` (`TranslationKeyExists` clean).
- [ ] **Schema strings translated** — `t:` keys in `en.default.schema.json`.
- [ ] **RTL mirrors** — set an RTL locale; layout mirrors correctly (logical properties, `dir` on `<html>`; no hard-coded left/right).

## I. SEO / structured data

- [ ] **Canonical + meta** — `canonical_url`, title/description present per template.
- [ ] **Structured data** — Product/Article/Breadcrumb JSON-LD emitted and valid.
- [ ] **Headings hierarchy** — single logical `<h1>` per page; ordered `h2`/`h3`.
- [ ] **Open Graph / social** — OG/Twitter tags via `content_for_header` + theme meta.

---

## Final summary table (fill in and emit)

| Area | Pass/Fail | Notes |
|------|-----------|-------|
| 0. Reliability & sync (no `{% stylesheet %}`, block names ≤ 25, valid roles, no cruft) | | |
| A. Shopify compliance | | |
| B. Settings control (incl. "No code required by merchant", "Shopify standards compliant") | | |
| C. OS 2.0 architecture | | |
| D. Liquid quality | | |
| E. Design system / tokens | | |
| F. Accessibility | | |
| G. Performance | | |
| H. i18n & RTL | | |
| I. SEO / structured data | | |
| `shopify theme check` (0 errors) | | |
| `scripts/validate_theme.py` | | |

Overall: **PASS / FAIL** — do not hand off on any FAIL.
