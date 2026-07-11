# Reliability & Sync — Landmines That Pass `theme-check` But Break The Store

`theme-check` is necessary but **not sufficient**. The failures below all pass
`theme-check` with zero offenses, yet break the theme once it is uploaded — a
silently dropped section, a 404 product page, a color system the editor refuses
to register, an add-to-cart that errors, a page that scrolls sideways on mobile.
These are the number-one cause of "it validated but the implementation is bad."

**Every rule here is mandatory.** They are encoded as automated checks in
`scripts/validate_theme.py` — run it in Phase 6 alongside `shopify theme check`.
Each entry is: **symptom → root cause → the rule.**

---

## 1. `{% stylesheet %}` / `{% javascript %}` are silently DROPPED by the importer ⚠️ #1 killer

**Symptom:** Sections you built render as "section type not found," templates that
reference them 404, the header/large parts of the theme go missing after a zip
upload or GitHub sync — even though the files are correct on disk and
`theme-check` is clean.

**Root cause:** Shopify's theme *importer* (both zip upload and the GitHub
integration) runs a stricter CSS/JS extractor than `theme-check`. Any section
file that uses the `{% stylesheet %}` or `{% javascript %}` tag can be **rejected
and dropped from the imported theme without any error surfaced to you.** Every
template or section group that referenced a dropped section then cascade-drops
too. This is how "18 sections vanished, product pages 404'd" happens.

**The rule — never emit `{% stylesheet %}` or `{% javascript %}` in a section or snippet.**

- Section-scoped CSS → use the **`{% style %}`** tag (inline `<style>`, survives
  the importer). Scope every rule under the section wrapper (`#Foo-{{ section.id }}`
  or a unique class) so nothing leaks.
- Shared/large CSS → an external file `assets/*.css` loaded with
  `{{ 'x.css' | asset_url | stylesheet_tag }}`. (The **`stylesheet_tag` filter**
  is fine and unrelated — only the **`{% stylesheet %}` tag** is the hazard.)
- JS → an external `assets/*.js` file loaded with
  `<script src="{{ 'x.js' | asset_url }}" defer></script>`. Never the
  `{% javascript %}` tag.

Yes, `{% style %}` is not auto-minified the way `{% stylesheet %}` claims to be.
Reliability beats a few unminified bytes. Keep section CSS lean; put anything
large in an external asset.

---

## 2. Section block `name` longer than 25 chars ⇒ section + template dropped ⇒ 404

**Symptom:** A whole template (e.g. product) 404s; the editor says "template not
found"; `theme-check` is clean and the file is on disk.

**Root cause:** Shopify's sync validation **rejects any section `{% schema %}`
block whose `name` exceeds 25 characters** (`theme-check` does NOT flag this).
The section is dropped on every sync, and any template referencing it dies with
it.

**The rule — every block `name` (and preset/section names, to be safe) is ≤ 25 characters.**
Count them. `"Rating (reviews metafield)"` (26) is rejected; `"Rating (reviews)"` (16)
is fine. Prefer `t:` locale keys for names — the KEY is what counts, so keep keys
short too, and verify the resolved English string is also short.

---

## 3. Invalid `color_scheme_group` role key ⇒ the ENTIRE color system is rejected

**Symptom:** Editor shows "color schemes must be defined in settings_data and
settings_schema files"; the storefront falls back to **serif system fonts**;
color settings do nothing. `theme-check` is clean (it does not validate role keys).

**Root cause:** The `role` object of a `color_scheme_group` accepts only a fixed
set of documented role keys. **One unknown key (e.g. `"shadow"`) invalidates the
whole group,** so Shopify registers *zero* schemes — which also breaks font
registration, hence the serif fallback.

**The rule — the `role` object uses ONLY these keys, nothing else:**
`background` (with `solid` / `gradient`), `text`, `primary_button`,
`on_primary_button`, `primary_button_border`, `secondary_button`,
`on_secondary_button`, `secondary_button_border`, `links`, `icons`.
No `shadow`, no invented keys. When in doubt, copy Dawn's `role` object verbatim.

> If a project prefers **direct color pickers** over scheme groups, that is a
> valid alternative (drop the `color_scheme_group` entirely, emit each picker as
> a `--color-*` var in `css-variables.liquid`, and give sections a static
> `color-scheme-1` wrapper class). Just never ship a *malformed* scheme group.

---

## 4. Static `{% section %}` mixed with section groups in a layout ⇒ layout render aborts

**Symptom:** `Liquid error (layout/theme line NN): 'cart-drawer' is not a valid
section type`, and because the layout render aborts, `css-variables` never runs
→ serif fonts + "color scheme" warning as collateral damage.

**Root cause:** `layout/theme.liquid` must not mix a **static singular**
`{% section 'x' %}` tag with section **groups** (`{% sections 'header-group' %}`).
Shopify rejects the combination and aborts the layout.

**The rule — in `layout/*.liquid`, deliver header, footer, AND the cart drawer
through section groups** (`{% sections 'header-group' %}` /
`{% sections 'footer-group' %}`). Put the cart drawer *inside* `footer-group.json`;
do not add a static `{% section 'cart-drawer' %}` to the layout. Guard the drawer
body on `settings.cart_type == 'drawer'`.

---

## 5. `| escape` (any filter) inside an `image_tag` argument ⇒ LiquidHTMLSyntaxError

**Symptom:** `LiquidHTMLSyntaxError` on a line that builds an image; only shows on
render/sync, not always in `theme-check`.

**Root cause:** You cannot pipe a filter inside an argument you pass to the
`image_tag` filter — e.g. `| image_tag: alt: image.alt | escape`. The parser
chokes on the nested `|`.

**The rule — pre-compute the value, then pass the plain variable:**
```liquid
{%- assign alt = image.alt | default: product.title | escape -%}
{{ image | image_url: width: 800 | image_tag: alt: alt, ... }}
```
(`| escape` in a normal HTML attribute like `alt="{{ x | escape }}"` is fine —
the hazard is *only* filters nested inside `image_tag` arguments.)

---

## 6. Single-variant products get no hidden variant `id` ⇒ add-to-cart / Buy-Now fail

**Symptom:** "Required parameter missing or invalid: items" on add-to-cart, and
dynamic checkout (Buy it now) silently does nothing — but only on products with
**one** variant.

**Root cause:** A variant-picker block only renders the hidden `id` input for
**multi-variant** products (it early-outs on `product.has_only_default_variant`).
Single-variant products then POST with no variant id.

**The rule — always emit the selected variant id.** Either use a
`<select name="id">` listing all variants (works for 1 or many, see the skeleton
`main-product.liquid`), or, if the picker only renders for multi-variant products,
add a hidden fallback in the buy-buttons form:
```liquid
{%- unless has_multi_variant_picker -%}
  <input type="hidden" name="id" value="{{ current_variant.id }}">
{%- endunless -%}
```
A defensive JS backfill (set the id on submit if missing) is a good belt-and-braces.

---

## 7. Custom elements default to `display: inline` ⇒ padding/height/margins ignored

**Symptom:** A web component (`<cart-drawer>`, `<product-recommendations>`,
`<recently-viewed>`, `<predictive-search>`, …) has no vertical spacing, collapses,
or its `padding-block` is simply ignored — leaving a stacked/broken layout.

**Root cause:** Unknown/custom elements render as `display: inline` by default, so
box-model properties don't apply.

**The rule — every custom element you define gets an explicit display in CSS:**
```css
cart-drawer, product-recommendations, recently-viewed, predictive-search { display: block; }
```
Add the rule in `base.css` (or the section's `{% style %}`) for *every*
`customElements.define('x-y', …)` you ship.

---

## 8. Grid/flex children default to `min-width: auto` ⇒ wide child overflows the viewport

**Symptom:** Horizontal page scroll / sideways overflow on mobile, usually caused
by a product gallery slider, a scroll-snap carousel, an embedded widget, or a
long table forcing its column wider than the screen.

**Root cause:** A CSS Grid/flex track defaults to `min-width: auto` (won't shrink
below its content). A wide child (a horizontal scroller, a full-res image) forces
the whole track — and the page — past the viewport width.

**The rule — set `min-inline-size: 0` (and/or `min-width: 0`) on grid/flex
children that contain scrollers, media, or wide content;** for the specific
overflow container use `overflow-x: clip` and `max-inline-size: 100%`. In grid
templates prefer `grid-template-columns: minmax(0, 1fr) …` so tracks can shrink.
Media/gallery items especially: `.product-media { min-inline-size: 0; }`.

---

## 9. `transform: translateX()` does NOT mirror in RTL

**Symptom:** In an Arabic/RTL storefront a centered dot, arrow, marquee, or slide
sits off-position or slides the wrong way, even though everything looks right in LTR.

**Root cause:** Logical CSS (`inset-inline`, `margin-inline`) mirrors in RTL, but
`transform` does not — `translateX(-50%)` moves the same visual direction in both
LTR and RTL.

**The rule — don't rely on `translateX` for direction-sensitive positioning.**
Center with `inset-inline: 0; margin-inline: auto` and animate on `translateY`
only; for carousels compute scroll deltas from `getBoundingClientRect()` (not raw
`scrollLeft`, which is signed differently across browsers in RTL).

---

## 10. A `<script src>` written into section/block HTML does NOT run on section re-render

**Symptom:** A third-party widget (Tabby/Tamara/BNPL, reviews, etc.) works on hard
page load but is blank in the theme editor or after the Section Rendering API
swaps the section (add-to-cart, variant change, filter apply).

**Root cause:** When Shopify re-renders a section, `<script src>` tags inside the
returned HTML are inserted but **not executed** by the browser. So an SDK that
relies on auto-scanning the DOM never boots on re-render.

**The rule — inject third-party SDKs imperatively:** create the script with
`document.createElement('script')` from a custom element's `connectedCallback`,
then call the SDK's `refresh()`/`init()` (poll until the SDK global exists).
Re-run on the theme's `variant:change`/section-load events. Never depend on a
declarative `<script src>` inside re-rendered section HTML.

---

## 11. `| tail` / `| head` on `theme check` masks its exit code ⇒ broken themes ship

**Symptom:** You believe a build passed, but offenses slipped through because the
pipe swallowed the failure.

**Root cause:** In a pipeline the exit status is that of the *last* command, so
`shopify theme check | tail` reports success even when `theme check` failed.

**The rule — never pipe `theme check` into `tail`/`head`.** Run it plainly and
read `$?`, e.g.:
```bash
shopify theme check; echo "exit=$?"
```
Treat any non-zero exit as a hard failure.

---

## 12. Deprecated / invalid filters that only bite at runtime

- **`payment_icon_png_url`** is not a valid filter (it appears in some old
  `gift_card.liquid` copies). Render payment icons with the supported approach
  (`{{ type | payment_type_svg_tag }}` / `shop.enabled_payment_types`) instead.
- Prefer `image_url` + `image_tag` over `img_url`/`img_tag`; `render` over
  `include`. See `shopify-standards.md` §5.

**The rule — no invented filters.** If you can't find a filter in the official
Liquid reference, it doesn't exist; find the documented one.

---

## 13. Editor-managed JSON files (`index.json`, `*-group.json`, `settings_data.json`)

**Symptom:** Your pushes to `templates/index.json` or `sections/footer-group.json`
"don't take," cause merge conflicts, or get silently overwritten; a setting you
changed reverts.

**Root cause:** These files are **written by the theme editor**. When a merchant
is live in the customizer, Shopify writes its own copy back (to GitHub too), so
concurrent code-side edits collide or lose.

**The rule — prefer fixing behavior in section `.liquid` code, not in
editor-managed JSON.** When you must change JSON: (a) do it while no one is in the
editor, (b) expect two-way sync, and (c) remember that section `presets` only seed
**newly added** sections — to change an *existing* page you must edit that
template's saved `blocks`/`block_order`, not just the preset.

---

## 14. Packaging — never zip cruft into the theme

**Symptom:** The importer rejects the zip, or you ship a bloated/insecure theme.

**Root cause:** Stray files (`npm-cache/`, `node_modules/`, `.DS_Store`, `*.log`,
nested `*.zip`, `.shopify/`, VCS dirs) inside the theme root. Shopify also forbids
subfolders inside `assets/`, `snippets/`, `sections/` (except
`templates/customers/` and `templates/metaobject/`).

**The rule — the theme root contains ONLY:** `assets/ config/ layout/ locales/
sections/ snippets/ templates/` (plus optional `blocks/`) and nothing else. Zip
with **forward slashes**. Before packaging, delete every non-theme file. The
scaffold must not carry a `npm-cache/` — if one appears, remove it.

---

## 15. Never trust "validation is green" — verify the file actually landed

**Symptom:** A file passes `theme-check` locally but is missing on the store after
sync, with no error anywhere.

**Root cause:** Silent importer drops (see #1, #2, #3).

**The diagnosis method (when a file mysteriously won't appear on the store):**
push a trivial probe change to an *unrelated* file to confirm sync is flowing,
then query the theme's files (Admin API `theme.files` / GraphQL) to see whether
your file is actually present. To get the *exact* rejection reason, upsert the
file via the Admin API (`themeFilesUpsert`) — it returns the real
`FILE_VALIDATION_ERROR` (e.g. "block name too long (max 25)") that the zip/GitHub
path hides. Fix the reported construct, re-sync, and re-verify presence.

---

## Quick pre-handoff scan (all must be empty / green)

```bash
# 1. no {% stylesheet %} / {% javascript %} tags anywhere in sections/snippets
grep -rnE '\{%-?\s*(stylesheet|javascript)\s*-?%\}' sections snippets && echo "FAIL" || echo "ok"

# 2. no static singular {% section %} in layouts (groups only)
grep -rnE "\{%-?\s*section\s+'" layout && echo "FAIL" || echo "ok"

# 3. no cruft in the theme root
find . -maxdepth 2 \( -name npm-cache -o -name node_modules -o -name '*.log' -o -name '.DS_Store' -o -name '*.zip' \) -print

# 4. structural + landmine lint, then full check (read the exit codes!)
python scripts/validate_theme.py .; echo "validate exit=$?"
shopify theme check; echo "themecheck exit=$?"
```
Block-name length (#2) and color-scheme roles (#3) are checked by
`validate_theme.py`. Runtime items (#6–#10) are verified live in Phase 6 QA.
