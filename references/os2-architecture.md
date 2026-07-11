# Online Store 2.0 Architecture

You are building an Online Store 2.0 (OS 2.0) theme. This doc is your map of how the moving parts fit together: JSON templates, sections + `{% schema %}`, blocks (theme and app), section groups, app blocks/embeds, metafields, and static sections. Read this before you scaffold any template or section, then use the decision table at the end whenever you are unsure which primitive to reach for.

The golden rule that drives every choice: **zero hard-coded content**. Every string, image, link, color, and toggle a merchant might want to change must be a setting, a block, or a metafield surfaced through a setting — never a literal baked into Liquid. If a merchant cannot change it in the theme editor, you built it wrong.

---

## 1. The OS 2.0 mental model

```
layout/theme.liquid
  ├── {% sections 'header-group' %}   ← section group (JSON) → header, announcement, etc.
  ├── {{ content_for_layout }}        ← the page's JSON template renders here
  └── {% sections 'footer-group' %}   ← section group (JSON) → footer, newsletter, etc.

templates/<type>.json                 ← ordered list of section instances + their settings/blocks
  └── sections/*.liquid + {% schema %}
        └── blocks (typed, repeatable, merchant-added) + {"type":"@app"} app slots
```

Three layers you compose:

1. **Templates** (`templates/*.json`) decide *which sections appear and in what order* on a page type.
2. **Sections** (`sections/*.liquid`) are the reusable UI units. Their `{% schema %}` declares merchant-editable `settings`, `blocks`, and `presets`.
3. **Blocks** are the repeatable, reorderable, merchant-added content *inside* a section.

Section groups are a fourth layer for the shared chrome (header/footer) that lives in `layout/theme.liquid` and appears on every page.

---

## 2. JSON templates

A JSON template is a data file that lists section *instances*. It contains no markup. The theme editor reads and writes it directly, which is what makes sections drag-reorderable and every setting editable.

### Structure

```jsonc
{
  "sections": {
    "<instance-id>": {
      "type": "<section-filename-without-extension>",
      "settings": { /* section-level settings */ },
      "blocks": {
        "<block-id>": { "type": "<block-type>", "settings": { /* ... */ } }
      },
      "block_order": ["<block-id>", "..."]
    }
  },
  "order": ["<instance-id>", "..."]
}
```

- `sections` — a map of instance IDs → instance config. The ID is arbitrary but stable (the editor generates them; you pick readable ones in your starter templates).
- Each instance's `type` points at `sections/<type>.liquid`.
- `blocks` + `block_order` describe the blocks inside that instance and their order.
- `order` — the top-level array that fixes the render order of sections on the page.
- Optional top-level `layout` can be `"theme"` or `"none"` (rarely used; `"none"` renders without `theme.liquid`, e.g. a bare page).

### Full example: `templates/product.json`

```json
{
  "sections": {
    "main": {
      "type": "main-product",
      "blocks": {
        "vendor": { "type": "text", "settings": { "text": "{{ product.vendor }}", "text_style": "uppercase" } },
        "title":  { "type": "title" },
        "price":  { "type": "price" },
        "variant_picker": { "type": "variant_picker", "settings": { "picker_type": "button" } },
        "quantity": { "type": "quantity_selector" },
        "buy_buttons": { "type": "buy_buttons", "settings": { "show_dynamic_checkout": true } },
        "description": { "type": "description" },
        "share": { "type": "share", "settings": { "share_label": "t:sections.main-product.share" } },
        "app_slot": { "type": "@app" }
      },
      "block_order": [
        "vendor", "title", "price", "variant_picker",
        "quantity", "buy_buttons", "description", "share", "app_slot"
      ],
      "settings": {
        "enable_sticky_info": true,
        "gallery_layout": "stacked",
        "media_size": "large"
      }
    },
    "related": {
      "type": "related-products",
      "settings": {
        "heading": "t:sections.related-products.heading",
        "products_to_show": 4,
        "columns_desktop": 4
      }
    }
  },
  "order": ["main", "related"]
}
```

Note the metafield-friendly binding `"text": "{{ product.vendor }}"` — a setting value can be a Liquid string that the section resolves at render (dynamic sources). More on that in §7.

### Static vs dynamic sections

| Type | How it's rendered | Merchant can add/remove/reorder? | Use for |
|---|---|---|---|
| **Dynamic** (JSON template) | Listed in a `templates/*.json` `order` array | Yes — full editor control | Everything on a page body: main product, rich text, image-with-text, testimonials, etc. |
| **Static** | Hard-called in Liquid via `{% section 'name' %}` | No — fixed position, but its own settings/blocks are still editable | A section that must always exist in a fixed slot (rare in OS 2.0; e.g. a bespoke component inside a custom layout) |

Prefer dynamic sections. Reach for static (`{% section %}`) only when the section must live at a fixed point in hand-written Liquid that isn't part of a section group.

### `{% content_for 'blocks' %}` (theme blocks era)

Newer themes can nest **theme blocks** to arbitrary depth. In a section that hosts nestable theme blocks, you render the merchant's block tree with:

```liquid
{% content_for 'blocks' %}
```

This replaces manually looping `section.blocks` when you opt a section into the theme-blocks model (blocks declared as `{"type": "@theme"}` and `{"type": "@app"}` in the schema's `blocks` array). For most sections you will still loop `section.blocks` explicitly (see §4). Use `{% content_for 'blocks' %}` when you want Shopify to manage nested block rendering and reordering for you.

---

## 3. Sections and `{% schema %}` anatomy

A section is `sections/<kebab-name>.liquid`: Liquid markup, optional scoped CSS in a **`{% style %}`** tag (never `{% stylesheet %}`/`{% javascript %}` — the importer can silently drop the section; see `reliability-and-sync.md` §1), any JS via an external `assets/*.js` asset, and exactly one `{% schema %}` JSON block.

```liquid
{%- comment -%} sections/image-with-text.liquid {%- endcomment -%}
<section
  class="image-with-text color-{{ section.settings.color_scheme }} section"
  style="--section-padding-block: {{ section.settings.padding_block }}px;"
>
  <div class="page-width image-with-text__grid">
    {%- for block in section.blocks -%}
      {%- case block.type -%}
        {%- when 'heading' -%}
          <h2 {{ block.shopify_attributes }}>{{ block.settings.heading }}</h2>
        {%- when 'text' -%}
          <div {{ block.shopify_attributes }}>{{ block.settings.body }}</div>
        {%- when 'button' -%}
          <a class="button" href="{{ block.settings.link }}" {{ block.shopify_attributes }}>
            {{ block.settings.label }}
          </a>
      {%- endcase -%}
    {%- endfor -%}
  </div>
</section>

{% schema %}
{
  "name": "t:sections.image-with-text.name",
  "tag": "section",
  "class": "section-wrapper",
  "settings": [
    {
      "type": "color_scheme",
      "id": "color_scheme",
      "label": "t:settings.color_scheme",
      "default": "scheme-1"
    },
    {
      "type": "range",
      "id": "padding_block",
      "min": 0, "max": 120, "step": 4, "unit": "px",
      "label": "t:settings.padding_block",
      "default": 48
    }
  ],
  "blocks": [
    { "type": "heading", "name": "t:blocks.heading.name", "limit": 1,
      "settings": [ { "type": "text", "id": "heading", "label": "t:settings.heading", "default": "t:defaults.heading" } ] },
    { "type": "text", "name": "t:blocks.text.name",
      "settings": [ { "type": "richtext", "id": "body", "label": "t:settings.body" } ] },
    { "type": "button", "name": "t:blocks.button.name", "limit": 2,
      "settings": [
        { "type": "text", "id": "label", "label": "t:settings.label" },
        { "type": "url", "id": "link", "label": "t:settings.link" }
      ] }
  ],
  "max_blocks": 6,
  "presets": [
    {
      "name": "t:sections.image-with-text.presets.name",
      "blocks": [ { "type": "heading" }, { "type": "text" }, { "type": "button" } ]
    }
  ],
  "enabled_on": { "templates": ["index", "page", "collection"] }
}
{% endschema %}
```

### Schema attribute reference

| Key | Purpose | Notes |
|---|---|---|
| `name` | Editor label for the section | Use a `t:` key |
| `tag` | Wrapper element Shopify emits | `section` (default), `div`, `article`, `aside`, `header`, `footer`. Set to control semantics/CLS |
| `class` | Extra class on the Shopify wrapper | For styling the auto-generated wrapper |
| `settings` | Section-level merchant controls | Array of setting objects (see input types below) |
| `blocks` | Block *type definitions* available in this section | Each has `type`, `name`, `settings`, optional `limit` |
| `max_blocks` | Cap on total blocks in the section | Default 50; set intentionally |
| `presets` | Makes the section addable from the "Add section" menu, with default blocks/settings | **Required** for a merchant to add the section to any dynamic template |
| `default` | Default config when auto-included (theme setup) | Alternative to `presets`; rarely both |
| `enabled_on` | Restrict where the section can be used | `{ "templates": [...], "groups": [...] }` |
| `disabled_on` | Inverse of `enabled_on` | Cannot use both for the same axis |
| `limit` | Max instances of this section per template | e.g. `1` for a hero |

`enabled_on` / `disabled_on` `templates` values: `index`, `product`, `collection`, `list-collections`, `page`, `blog`, `article`, `cart`, `search`, `404`, `customers/*`, `password`, `gift_card`, `*` (all). `groups` values: `header`, `footer`, `aside`, or `custom.*`.

If a section has **no `presets` and no `default`**, merchants cannot add it via "Add section" — it can only be placed by editing JSON or included statically. That is intentional for `main-*` sections (which belong to a specific template) but a bug for a general-purpose section.

### Section-level styling from settings

Pass merchant settings into your design-token layer via inline custom properties on the wrapper, e.g. `style="--section-padding-block: {{ section.settings.padding_block }}px;"`, then consume `var(--section-padding-block)` in your `{% style %}` block. This keeps CSS static and cacheable while remaining merchant-driven.

---

## 4. Blocks

Blocks are the repeatable, merchant-orderable content inside a section. They come in three flavors.

### Typed (local) blocks

Defined in the section's schema `blocks` array; rendered by looping `section.blocks` and switching on `block.type`. Always emit `{{ block.shopify_attributes }}` on the block's root element so the theme editor can select, highlight, and reorder it live.

```liquid
{%- for block in section.blocks -%}
  {%- case block.type -%}
    {%- when 'icon' -%}
      <li class="feature" {{ block.shopify_attributes }}>
        {% render 'icon', name: block.settings.icon %}
        <span>{{ block.settings.label }}</span>
      </li>
  {%- endcase -%}
{%- endfor -%}
```

`{{ block.shopify_attributes }}` expands to `data-shopify-editor-block="..."` attributes. Omit it and the block becomes unselectable in the editor — a hard fail for "100% controllable from the editor."

### Theme blocks (`blocks/*.liquid`, `{"type":"@theme"}`)

Reusable block files living in the top-level `blocks/` directory, referenceable across sections and nestable. Declare acceptance in the section schema:

```json
"blocks": [
  { "type": "@theme" },
  { "type": "@app" }
]
```

and render the nested tree with `{% content_for 'blocks' %}` (see §2). A theme block file mirrors a section: markup + its own `{% schema %}` with `settings`, and may itself accept child blocks. Use these when you want a component (e.g. `blocks/button.liquid`) shared by many sections with one definition.

### App blocks (`{"type":"@app"}`)

An app block is a slot a merchant app fills (reviews widget, upsell, etc.). You **declare the slot**; the app provides the block. Add to the schema `blocks` array:

```json
"blocks": [
  { "type": "text" },
  { "type": "@app" }
]
```

When present, the "Add block" menu shows installed apps' blocks alongside your typed blocks. In the JSON template you leave a placeholder instance `{ "type": "@app" }` (as in the `product.json` example) so merchants have an app slot pre-positioned. Loop rendering handles app blocks automatically — they come through `section.blocks` with their own `block.type` and render via `{{ block.shopify_attributes }}` and the app's own output; you do not write markup for them.

**Always add an `{"type":"@app"}` slot to `main-product`, `main-collection`, and `main-cart`** so apps like reviews and upsells have a home without the merchant editing Liquid.

---

## 5. Section groups (header & footer)

Section groups let merchants edit the shared chrome (header, announcement bar, footer) in the theme editor with the same section/block model. They are JSON files in `sections/` and are rendered from the layout.

### `sections/header-group.json`

```json
{
  "type": "header",
  "name": "t:section_groups.header.name",
  "sections": {
    "announcement": {
      "type": "announcement-bar",
      "blocks": {
        "msg1": { "type": "announcement", "settings": { "text": "t:defaults.announcement" } }
      },
      "block_order": ["msg1"]
    },
    "header": {
      "type": "header",
      "settings": { "sticky_header_type": "on-scroll-up", "menu": "main-menu" }
    }
  },
  "order": ["announcement", "header"]
}
```

### `sections/footer-group.json`

```json
{
  "type": "footer",
  "name": "t:section_groups.footer.name",
  "sections": {
    "footer": {
      "type": "footer",
      "blocks": {
        "menu":       { "type": "link_list", "settings": { "menu": "footer" } },
        "newsletter": { "type": "newsletter" }
      },
      "block_order": ["menu", "newsletter"]
    }
  },
  "order": ["footer"]
}
```

- Top-level `"type"` must be `"header"` or `"footer"` (or `"aside"` / `"custom.<name>"`). This tells the editor which group it is and gates which sections `enabled_on.groups` permits.
- Structure is otherwise identical to a JSON template: `sections` map + `order` array.

### Rendering from `layout/theme.liquid`

```liquid
<body>
  {% sections 'header-group' %}
  <main id="MainContent" role="main">
    {{ content_for_layout }}
  </main>
  {% sections 'footer-group' %}
</body>
```

`{% sections 'header-group' %}` (plural — takes the group filename without `.json`) renders every section in that group in `order`. `{{ content_for_layout }}` is where the current page's JSON template renders. This is the standard Dawn arrangement; follow it.

---

## 6. App blocks & app embeds

Two distinct integration points for merchant apps — leave room for both:

| | **App block** | **App embed** |
|---|---|---|
| Where | Inside a section, via `{"type":"@app"}` slot | Floating/global, injected app-wide |
| Merchant adds via | "Add block" in a section | Theme editor → **App embeds** toggle |
| Renders where | In the section's block flow | Injected before `</body>` / `</head>` |
| You do | Add `{"type":"@app"}` to relevant sections' schema `blocks` | Nothing in section code — just ensure `{{ content_for_header }}` and the closing-body app scope work (they do by default in `theme.liquid`) |
| Examples | Product reviews under the buy button, upsell in cart | Klaviyo popups, cookie banner, chat widget, back-in-stock |

Checklist: (1) `{{ content_for_header }}` is in `<head>` of `theme.liquid` — required for app embeds and Shopify features; (2) `main-product`, `main-collection`, `main-cart` sections each expose `{"type":"@app"}`; (3) you never hard-code an app's markup — the merchant installs the app and places its block/embed themselves.

---

## 7. Metafield-driven content

Metafields let merchants attach structured data to products, collections, pages, etc., and you surface it — without hard-coding. Two ways to consume:

### A) Read directly in a section

```liquid
{%- assign care = product.metafields.custom.care_instructions -%}
{%- if care != blank -%}
  <div class="product__care">
    {%- if care.type == 'rich_text_field' -%}
      {{ care.value }}                {%- comment -%} rich_text renders as HTML {%- endcomment -%}
    {%- else -%}
      <p>{{ care.value }}</p>
    {%- endif -%}
  </div>
{%- endif -%}
```

Namespaced access: `resource.metafields.<namespace>.<key>`. Common types: `single_line_text_field`, `multi_line_text_field`, `rich_text_field` (has `.value` that outputs HTML), `number_integer`, `boolean`, `list.single_line_text_field` (iterate `.value`), `product_reference` / `variant_reference` / `file_reference` / `metaobject_reference` (`.value` is the referenced object). See `liquid-patterns.md` §metafields for full handling.

### B) Surface via a `metafield`/dynamic-source setting

OS 2.0 settings can bind to a metafield through **dynamic sources** (the "connect" ⚡ icon in the editor). Declare a text/richtext setting; merchants click the dynamic-source connector and pick a metafield. Your Liquid just outputs `{{ block.settings.body }}` and the platform resolves it to the metafield value. This is why the `product.json` example uses `"text": "{{ product.vendor }}"` — that is a dynamic-source binding, not a literal.

### Defining metafields

Metafield *definitions* are created in Shopify admin (Settings → Custom data) or via the Admin API / `graphql_mutation` (`metafieldDefinitionCreate`). Your theme does not define them, but your docs/onboarding should tell merchants which namespaces/keys the theme reads (e.g. `custom.care_instructions`, `custom.ingredients`) so they know what to populate. Guard every metafield read with `!= blank` so a store without the definition degrades gracefully.

---

## 8. Static sections

Use `{% section 'name' %}` (singular) to hard-render one section at a fixed spot in Liquid — outside any JSON template's control:

```liquid
{% comment %} in a custom layout or a template's own liquid, rarely {% endcomment %}
{% section 'breadcrumbs' %}
```

The section's own settings/blocks remain editable in the editor, but merchants cannot move or remove the section, and it appears wherever you called it. In OS 2.0 you rarely need this — section groups and JSON templates cover header, footer, and body. Reach for it only for a fixed structural element that genuinely must not be reorderable and is not part of a section group.

---

## 9. Decision table: JSON template vs section vs block vs section group

| You need to… | Use | Why |
|---|---|---|
| Define what appears on a **page type** (product, collection, page, index) and in what order | **JSON template** (`templates/*.json`) | Merchant reorders/adds/removes sections in the editor |
| Create a **reusable page-body UI unit** a merchant can add anywhere | **Section** with `presets` | Presets make it addable; dynamic placement |
| Bind a section to **one specific template** and prevent it being added elsewhere | **Section** without `presets`, named `main-<type>`, `enabled_on.templates` | e.g. `main-product` only on product |
| Add **repeatable, reorderable content inside** a section (list of features, slides, FAQ items) | **Blocks** (typed or `@theme`) | Merchant adds N of them, reorders, each with its own settings |
| Share **one component definition across many sections**, possibly nested | **Theme block** (`blocks/*.liquid`, `@theme`) + `{% content_for 'blocks' %}` | Single source, reusable, nestable |
| Give a **merchant app** a place to render inside a section | **App block slot** `{"type":"@app"}` in schema + placeholder in JSON | Reviews, upsells, etc. |
| Let a merchant enable a **global/floating app feature** | **App embed** (nothing to code; ensure `content_for_header`) | Klaviyo, chat, cookie banner |
| Edit the **header/announcement/footer** shared across all pages | **Section group** (`header-group.json` / `footer-group.json`) rendered via `{% sections %}` | Shared chrome, editor-controlled |
| Place a section at a **fixed, non-reorderable spot** in hand-written Liquid | **Static section** `{% section 'name' %}` | Rare; only when JSON template/section group won't do |
| Surface **merchant-entered structured data** without hard-coding | **Metafield** read (guarded) or dynamic-source setting | Ingredients, care, specs |

Default bias: **JSON template + sections + presets + blocks**. Escalate to theme blocks for shared/nested components, section groups for chrome, static sections almost never.
