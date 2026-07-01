# Settings Control — 100% Theme-Editor Controllable, Zero Merchant Code

**Core rule:** If a piece of content or styling is not wired to a **setting**, **block**, or **section group**, the section is **NOT done**. A merchant must be able to change every string, image, color, link, font, and spacing value from the theme editor without touching code. See [shopify-standards.md](./shopify-standards.md) and [qa-checklist.md](./qa-checklist.md).

---

## 1. Input-type catalog — when to use each

| Type | Use for |
|------|---------|
| `text` | Short single-line strings (headings, labels, button text) |
| `textarea` | Multi-line plain text (short descriptions) |
| `richtext` | Formatted paragraph content (bold/italic/links/lists) — block-level |
| `inline_richtext` | Formatted inline text with no wrapping `<p>` (headings you style) |
| `html` | Raw HTML/embeds (use sparingly; merchant-owned markup) |
| `liquid` | Merchant-supplied Liquid (custom snippets) |
| `image_picker` | Any image (logo, hero, banners) — returns an image object |
| `video` | Shopify-hosted video (returns media object) |
| `video_url` | External YouTube/Vimeo URL |
| `url` | Any link target (internal or external) |
| `link_list` | A menu (returns `linklists[...]`) for nav/footer |
| `product` | Single product reference |
| `product_list` | Multiple products (featured grids) — set `limit` |
| `collection` | Single collection reference |
| `collection_list` | Multiple collections — set `limit` |
| `blog` | A blog reference |
| `article` | A single article reference |
| `page` | A page reference (pull page content into a section) |
| `color` | Single color value (prefer color_scheme for surfaces) |
| `color_scheme` | Pick one Dawn-style scheme for a section |
| `color_scheme_group` | Define the set of schemes (theme settings only) |
| `font_picker` | Heading/body font (feeds `--font-*-family`) |
| `select` | Named choice (layout style, alignment) with `options` |
| `radio` | Small mutually-exclusive choice |
| `range` | Numeric with min/max/step/unit (spacing, padding, columns) |
| `checkbox` | Boolean show/hide toggle |
| `number` | Free numeric (rarely — prefer `range`) |
| `header` | Visual group divider (organizes the panel) |
| `paragraph` | Static helper/explainer text in the editor |

---

## 2. Blocks pattern

Repeatable content = **blocks**, never hard-coded loops of markup.

```liquid
<div class="feature-grid" {{ section.shopify_attributes }}>
  {%- for block in section.blocks -%}
    {%- case block.type -%}
      {%- when 'feature' -%}
        <article class="feature" {{ block.shopify_attributes }}>
          {%- if block.settings.icon != blank -%}
            <img src="{{ block.settings.icon | image_url: width: 96 }}"
                 width="{{ block.settings.icon.width }}"
                 height="{{ block.settings.icon.height }}"
                 alt="{{ block.settings.icon.alt | escape }}" loading="lazy">
          {%- endif -%}
          <h3>{{ block.settings.title | escape }}</h3>
          <div class="rte">{{ block.settings.text }}</div>
        </article>
    {%- endcase -%}
  {%- endfor -%}
</div>
```

- Always emit `{{ block.shopify_attributes }}` on each block's root element (editor selection/drag).
- Use `{{ section.shopify_attributes }}` on the section root.
- Set `max_blocks` when there's a sensible cap.
- Include `{ "type": "@app" }` so merchants can insert app blocks.

---

## 3. Show/hide, spacing, and layout controls

Expose these as first-class settings so nothing needs code:

```json
{ "type": "checkbox", "id": "show_heading", "label": "t:settings.show_heading", "default": true },
{ "type": "select",   "id": "layout", "label": "t:settings.layout",
  "options": [
    { "value": "grid",  "label": "t:settings.layout_grid" },
    { "value": "slider","label": "t:settings.layout_slider" }
  ], "default": "grid" },
{ "type": "range", "id": "padding_top", "min": 0, "max": 100, "step": 4, "unit": "px",
  "label": "t:settings.padding_top", "default": 40 },
{ "type": "range", "id": "columns", "min": 1, "max": 5, "step": 1,
  "label": "t:settings.columns", "default": 3 }
```

Wire spacing to the token layer, e.g. inline style hooks that feed CSS variables:

```liquid
<section class="section" style="--section-padding-block: {{ section.settings.padding_top }}px;">
```

---

## 4. Sensible defaults so nothing looks broken empty

- Give every text/image/link setting a `default` (or a `{% if setting != blank %}` fallback).
- Provide `presets` with `default` blocks so a freshly added section renders a complete, attractive layout immediately.
- Guard every optional field: `{%- if section.settings.image != blank -%}`.

---

## 5. Grouping with `header` + `info`

Organize the panel and explain non-obvious settings:

```json
{ "type": "header", "content": "t:settings.headers.layout" },
{ "type": "range", "id": "grid_gap", "label": "t:settings.grid_gap",
  "info": "t:settings.grid_gap_info", "min": 0, "max": 48, "step": 4, "unit": "px", "default": 16 }
```

Every setting has a `label`; non-obvious ones have `info`; related settings sit under a `header`.

---

## 6. "No hard-coded X" audit table

If any row maps to literal text/markup in Liquid, it FAILS. Every row must map to a setting.

| Concern | Must map to |
|---------|-------------|
| Text / headings / labels | `text` / `inline_richtext` / `richtext` setting |
| Body copy | `richtext` setting |
| Colors / surfaces | `color_scheme` (section) + token vars — never literal hex |
| Images | `image_picker` (or `product`/`collection` media) |
| Videos | `video` / `video_url` |
| Links / buttons | `url` setting |
| Menus / navigation | `link_list` setting |
| Fonts | `font_picker` → `--font-*-family` |
| Spacing / padding / columns | `range` settings → token vars |
| Show/hide of any element | `checkbox` |
| Layout / alignment variants | `select` / `radio` |
| Products / collections shown | `product`/`collection`(`_list`) settings |

---

## 7. Copy-paste section schema (headers + blocks + preset)

```liquid
{% schema %}
{
  "name": "t:sections.feature_grid.name",
  "tag": "section",
  "class": "section",
  "max_blocks": 8,
  "settings": [
    { "type": "header", "content": "t:settings.headers.content" },
    { "type": "inline_richtext", "id": "heading", "label": "t:settings.heading",
      "default": "Featured" },
    { "type": "checkbox", "id": "show_heading", "label": "t:settings.show_heading", "default": true },
    { "type": "header", "content": "t:settings.headers.layout" },
    { "type": "select", "id": "layout", "label": "t:settings.layout",
      "options": [
        { "value": "grid", "label": "t:settings.layout_grid" },
        { "value": "slider", "label": "t:settings.layout_slider" }
      ], "default": "grid" },
    { "type": "range", "id": "columns", "label": "t:settings.columns",
      "min": 1, "max": 5, "step": 1, "default": 3 },
    { "type": "header", "content": "t:settings.headers.appearance" },
    { "type": "color_scheme", "id": "color_scheme", "label": "t:settings.color_scheme",
      "default": "scheme-1" },
    { "type": "range", "id": "padding_block", "label": "t:settings.padding_block",
      "info": "t:settings.padding_block_info",
      "min": 0, "max": 120, "step": 4, "unit": "px", "default": 48 }
  ],
  "blocks": [
    {
      "type": "feature",
      "name": "t:sections.feature_grid.blocks.feature.name",
      "settings": [
        { "type": "image_picker", "id": "icon", "label": "t:settings.icon" },
        { "type": "text", "id": "title", "label": "t:settings.title", "default": "Feature" },
        { "type": "richtext", "id": "text", "label": "t:settings.text",
          "default": "<p>Describe this feature.</p>" },
        { "type": "url", "id": "link", "label": "t:settings.link" }
      ]
    },
    { "type": "@app" }
  ],
  "presets": [
    {
      "name": "t:sections.feature_grid.presets.name",
      "blocks": [
        { "type": "feature" },
        { "type": "feature" },
        { "type": "feature" }
      ]
    }
  ]
}
{% endschema %}
```

---

## 8. Per-section "done" checklist

A section is done only when:

- [ ] Every string, image, link, color, font, spacing value maps to a setting (§6 audit passes)
- [ ] Colors come from `color_scheme` + tokens — no literal hex in the section
- [ ] Fonts come from `font_picker`/theme tokens
- [ ] Spacing/padding/columns are `range` settings feeding token vars
- [ ] Repeated content uses **blocks** with `{{ block.shopify_attributes }}`
- [ ] `{{ section.shopify_attributes }}` on the section root
- [ ] `{ "type": "@app" }` block present
- [ ] Optional fields guarded with `!= blank`; sensible `default`s everywhere
- [ ] Settings grouped under `header`s; non-obvious ones have `info`
- [ ] Every label/info/option is a `t:` key in `en.default.schema.json`
- [ ] A `presets` entry with default blocks renders a complete look out of the box
- [ ] Show/hide toggles and layout selects exposed where relevant
