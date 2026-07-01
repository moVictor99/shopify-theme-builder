# Shopify Standards — Hard Rules You Must Satisfy

You are building an Online Store 2.0 (OS 2.0) theme that must pass `theme-check` with **zero errors** and clear the **Shopify Theme Store** review bar. Treat everything below as non-negotiable. When in doubt, mirror **Dawn**. See also [settings-control.md](./settings-control.md) and [qa-checklist.md](./qa-checklist.md).

---

## 1. Required directory structure

Your theme MUST use exactly these top-level directories (no others):

```
theme/
├── assets/            # css, js, svg, images, fonts (flat — no subfolders)
├── config/
│   ├── settings_schema.json    # REQUIRED — theme settings definition
│   └── settings_data.json      # REQUIRED — saved setting values + presets
├── layout/
│   ├── theme.liquid            # REQUIRED — main layout
│   └── password.liquid         # REQUIRED — storefront password page
├── locales/
│   ├── en.default.json         # REQUIRED — default storefront strings
│   └── en.default.schema.json  # REQUIRED — default editor/schema strings
├── sections/
│   ├── header-group.json       # section group
│   └── footer-group.json       # section group
├── snippets/
└── templates/
    ├── customers/              # customer.* templates live here
    └── *.json                  # JSON templates (OS 2.0)
```

`assets/` must be flat — Shopify does not allow nested folders inside `assets/`, `snippets/`, `sections/`, `templates/` (except `templates/customers/` and `templates/metaobject/`).

---

## 2. Required files & templates

`theme-check` and the Theme Store both require these to exist. Prefer **JSON** templates (OS 2.0) so every page is section-driven and editable.

| File | Required | Notes |
|------|----------|-------|
| `config/settings_schema.json` | ✅ | Must start with the `theme_info` object |
| `config/settings_data.json` | ✅ | `current` + `presets` keys |
| `layout/theme.liquid` | ✅ | Must contain `{{ content_for_header }}` and `{{ content_for_layout }}` |
| `layout/password.liquid` | ✅ | Must contain `{{ content_for_header }}` and `{{ content_for_layout }}` |
| `locales/en.default.json` | ✅ | Storefront strings |
| `locales/en.default.schema.json` | ✅ | Schema/editor strings |
| `templates/index.json` | ✅ | Home |
| `templates/product.json` | ✅ | Product |
| `templates/collection.json` | ✅ | Collection |
| `templates/list-collections.json` | ✅ | All collections |
| `templates/page.json` | ✅ | Generic page |
| `templates/blog.json` | ✅ | Blog listing |
| `templates/article.json` | ✅ | Article |
| `templates/cart.json` | ✅ | Cart |
| `templates/search.json` | ✅ | Search results |
| `templates/404.json` | ✅ | Not found |
| `templates/password.json` | ✅ | Password landing (paired with `layout/password.liquid`) |
| `templates/gift_card.liquid` | ✅ | Gift card (this one stays `.liquid`) |
| `templates/customers/account.json` | ✅ | Also: `activate_account`, `addresses`, `login`, `order`, `register`, `reset_password` |

Optional but recommended variants: `templates/product.<name>.json`, `templates/collection.<name>.json`, `templates/page.<name>.json` for merchant-selectable alternates.

---

## 3. theme-check MUST pass with zero errors

Run `shopify theme check` (a.k.a. `theme-check`) in CI and before every hand-off. Key checks you must never trip:

| Check | What it enforces |
|-------|------------------|
| `ValidSchema` | Every `{% schema %}` is valid JSON with valid setting/block definitions |
| `ValidJSON` | All `.json` files parse |
| `LiquidTag` / `SyntaxError` | No malformed Liquid |
| `UnknownFilter` | No unknown/typo'd filters |
| `DeprecatedFilter` | No deprecated filters (see table §5) |
| `DeprecatedTag` | No deprecated tags (`{% include %}`) |
| `ImgLazyLoading` | Below-the-fold `<img>` has `loading="lazy"` |
| `ImgWidthHeight` | Every `<img>` has `width` and `height` (prevents CLS) |
| `AssetSizeCSS` / `AssetSizeJS` | Bundled CSS/JS under size budget |
| `AssetSizeAppBlockCSS/JS` | App block assets under budget |
| `RemoteAsset` | No hard-coded remote asset URLs; use `asset_url` |
| `UnusedAssign` | No dead `{% assign %}` |
| `UnusedSnippet` | No orphan snippets |
| `TranslationKeyExists` | Every `t:` / `{{ '...' | t }}` key exists in locales |
| `MissingTemplate` | Referenced templates/snippets exist |
| `RequiredLayoutThemeObject` | `theme.liquid` has `content_for_header` + `content_for_layout` |
| `ParserBlockingScript` | No parser-blocking `<script src>` (use `defer`) |
| `ContentForHeaderModification` | Don't parse/mutate `content_for_header` |
| `ValidHTMLTranslation` | Translations with HTML are valid |
| `SchemaPresetsStaticBlocks` | Preset blocks reference declared block types |

Zero **errors** is mandatory. Drive warnings toward zero too.

---

## 4. Layout requirements

`layout/theme.liquid` skeleton (mirror Dawn):

```liquid
<!doctype html>
<html lang="{{ request.locale.iso_code }}" dir="{% render 'direction' %}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="theme-color" content="">
    <link rel="canonical" href="{{ canonical_url }}">
    {{ content_for_header }}   {%- comment -%} MUST be present, unmodified {%- endcomment -%}
    {{ 'base.css' | asset_url | stylesheet_tag }}
    <script src="{{ 'global.js' | asset_url }}" defer="defer"></script>
  </head>
  <body>
    {% sections 'header-group' %}
    <main id="MainContent" role="main" tabindex="-1">
      {{ content_for_layout }}   {%- comment -%} MUST be present {%- endcomment -%}
    </main>
    {% sections 'footer-group' %}
  </body>
</html>
```

- Never modify or `split`/`replace` `content_for_header` (`ContentForHeaderModification`).
- Header and footer must be delivered via **section groups** (`{% sections 'header-group' %}`), not hard-coded.

---

## 5. No deprecated Liquid — modernization table

| Deprecated | Use instead |
|-----------|-------------|
| `{% include 'x' %}` | `{% render 'x' %}` (isolated scope; pass vars explicitly) |
| `img_url` filter | `image_url` (requires `width:`) |
| `img_tag` (old signature) | `image_tag` with `width`/`height`/`loading` |
| `{{ img | img_url: '300x' }}` | `{{ img | image_url: width: 300 | image_tag }}` |
| `collection.products` w/ no pagination | `paginate` + `{{ paginate }}` |
| `{% schema %}` hard-coded home content | `templates/index.json` sections |
| `product.featured_image` (legacy alias) | `product.featured_media` / `.featured_image` OK but prefer media |
| `handle` on deleted objects | current objects; avoid `shop.metafields` undocumented paths |
| Global `{% javascript %}`/`{% stylesheet %}` in sections for large code | External `assets/*.js` / `*.css` with `asset_url` |
| `{% section 'x' %}` for header/footer | Section groups (`sections/*-group.json`) |
| `where`/manual filtering when a filter object exists | `search`/`filters`/`storefront_filters` |

Rules of thumb: `render` over `include`; `image_url` over `img_url`; JSON templates over `.liquid` templates; section groups over static sections.

---

## 6. Images & media

Every image must be responsive and CLS-safe:

```liquid
{% assign sizes = '(min-width: 990px) 50vw, 100vw' %}
<img
  src="{{ image | image_url: width: 800 }}"
  srcset="{{ image | image_url: width: 400 }} 400w,
          {{ image | image_url: width: 800 }} 800w,
          {{ image | image_url: width: 1200 }} 1200w"
  sizes="{{ sizes }}"
  width="{{ image.width }}"
  height="{{ image.height }}"
  alt="{{ image.alt | escape }}"
  loading="lazy">
```

- Above-the-fold LCP image: `loading="eager"` + `fetchpriority="high"`; everything else `loading="lazy"`.
- Always emit `width` + `height` (or CSS `aspect-ratio`) to prevent layout shift.
- Never hot-link remote images; upload to assets or use image_picker settings.

---

## 7. Scripts & performance

- All `<script src>` must use `defer="defer"` (or `type="module"`, which defers by design). No parser-blocking scripts.
- Vanilla JS only, `type="module"`, custom elements, event delegation. No jQuery, no globals.
- Keep per-asset CSS/JS under theme-check size budgets; split large bundles.
- Lazy-load offscreen sections' heavy assets.

**Theme Store performance bar** (Lighthouse-based, measured on home, product, collection):
- Meet Core Web Vitals: good **LCP**, low **CLS**, responsive **INP**.
- No render-blocking resources beyond critical CSS.
- No console errors or 404s on any template.

---

## 8. `{% schema %}`, presets & app support

Every section needs a valid `{% schema %}` with a `presets` entry so it appears in the theme editor's "Add section" list:

```json
{% schema %}
{
  "name": "t:sections.example.name",
  "tag": "section",
  "class": "section",
  "settings": [],
  "blocks": [
    { "type": "@app" }
  ],
  "presets": [
    { "name": "t:sections.example.presets.name", "blocks": [] }
  ]
}
{% endschema %}
```

- Include `{ "type": "@app" }` in `blocks` on content sections so merchants can drop in **app blocks**.
- Support **app embed blocks** by keeping `{{ content_for_header }}` intact (Shopify injects app embeds there).
- Every user-facing string in the schema uses a `t:` key present in `en.default.schema.json`.

---

## 9. i18n

- Storefront strings: `{{ 'key' | t }}` → `locales/en.default.json`.
- Schema/editor strings: `t:` keys → `locales/en.default.schema.json`.
- Set `dir` for RTL locales; do not hard-code `left`/`right` — use logical properties (`margin-inline-start`, etc.).

---

## 10. Compliance gate — final checklist

Do not hand off unless every box is checked:

- [ ] All required directories/files present (§1, §2)
- [ ] All JSON templates exist incl. `customers/*`
- [ ] `layout/theme.liquid` + `layout/password.liquid` have `content_for_header` & `content_for_layout`
- [ ] Header/footer delivered via section groups
- [ ] `shopify theme check` → **0 errors** (§3)
- [ ] No deprecated filters/tags (§5) — `include`→`render`, `img_url`→`image_url`
- [ ] Every `<img>` has `width`+`height`+ srcset + lazy (except LCP) (§6)
- [ ] All `<script>` use `defer`/`type="module"`; no parser-blocking JS (§7)
- [ ] Every section has valid `{% schema %}` + `presets` + `@app` block (§8)
- [ ] `@app` app blocks and app embeds supported
- [ ] Every string is a translation key; `en.default.json` + `en.default.schema.json` complete (§9)
- [ ] No console errors/404s on any template
- [ ] Lighthouse/CWV pass on home, product, collection (§7)
- [ ] `config/settings_schema.json` opens with `theme_info`; `settings_data.json` has presets
