# Internationalization (i18n) + RTL

This is your reference for building a Shopify theme where **every shopper-facing string is translatable** and where **Right-to-Left (Arabic) is a first-class layout**, not a bolt-on. Treat bilingual EN/AR + full RTL as the baseline you always build to, even when the first store ships English-only — because retrofitting RTL later means rewriting every stylesheet.

Two hard rules govern everything below:

1. **Never hard-code a shopper-facing string.** If a human reading the storefront can see it, it lives in a locale file and is rendered through the `t` filter / translation key. This includes button labels, aria-labels, empty-states, error messages, and placeholder text.
2. **Never write a physical direction in CSS** (`left`, `right`, `margin-left`, `padding-right`, `text-align: left`, `float`). Use CSS **logical properties** so the same rule flows correctly in both LTR and RTL.

---

## 1. Locale file structure

Shopify splits translations into **two file families** that live in `locales/`:

| File | Purpose | Where it's used |
| --- | --- | --- |
| `locales/en.default.json` | **Storefront strings** — everything the shopper reads | `{{ 'key' \| t }}`, `{{ 't:key' }}`, section/snippet Liquid |
| `locales/en.default.schema.json` | **Theme-editor labels** — settings, section names, option labels the merchant reads in the customizer | `"label": "t:names..."` inside `{% schema %}` and `settings_schema.json` |
| `locales/ar.json` | Arabic storefront strings (mirror of `en.default.json`) | same keys, Arabic values |
| `locales/ar.schema.json` | Arabic theme-editor labels (mirror of `en.default.schema.json`) | same keys, Arabic values |

Rules:

- Exactly **one** default storefront file (`*.default.json`) and **one** default schema file (`*.default.schema.json`). The `.default` marker tells Shopify which locale to fall back to.
- Every non-default locale is `<iso>.json` + `<iso>.schema.json` (e.g. `ar.json`, `fr.json`, `es.json`). Missing keys fall back to the default file automatically — so the default file must be **complete**.
- Keys must be **identical across all locale files**. Run `theme-check` (`TranslationKeyExists`) to catch drift. A key present in `ar.json` but absent from `en.default.json` is an error.
- Schema files may **only** be referenced from `{% schema %}` blocks and `config/settings_schema.json`; storefront files may **only** be referenced from Liquid/`t`. Do not cross them.

---

## 2. Key namespacing convention

Namespace keys by domain so they stay discoverable and collide-free. Mirror Dawn's taxonomy:

| Namespace | Contains | Example key |
| --- | --- | --- |
| `general.*` | Site-wide chrome, shared words | `general.search.search`, `general.pagination.next` |
| `sections.*` | Per-section strings, grouped by section | `sections.header.menu`, `sections.cart.title` |
| `products.*` | Product page + card | `products.product.add_to_cart`, `products.product.sold_out` |
| `cart.*` | Cart + checkout-adjacent | `cart.general.subtotal`, `cart.general.empty` |
| `customer.*` | Account, login, register, addresses | `customer.login.title`, `customer.orders.date` |
| `blogs.*` / `templates.*` | Blog, article, 404, contact, search page | `templates.404.title`, `blogs.article.comments` |
| `accessibility.*` | Visually-hidden + aria strings | `accessibility.skip_to_text`, `accessibility.close` |
| `newsletter.*`, `gift_cards.*`, `localization.*` | Feature pockets | `localization.country_label` |

Convention: `namespace.group.string` — lowercase, `snake_case` leaves, dot-separated. Keep the tree shallow (3 levels max).

---

## 3. Rendering strings in Liquid

### The `t` filter (canonical form)

```liquid
{{ 'products.product.add_to_cart' | t }}
```

### The `{{ 't:key' }}` shorthand

Shopify also accepts the `t:` prefix inside contexts that resolve translation keys directly (schema defaults, some setting values). In Liquid template code, **prefer the explicit `| t` filter** — it is unambiguous and what `theme-check` expects:

```liquid
<button type="submit" name="add">
  {{ 'products.product.add_to_cart' | t }}
</button>
```

### With `{% render %}`

Pass already-translated strings, or pass keys and translate inside the snippet. Preferred: translate at the point of display.

```liquid
{% render 'price', product: product %}
{%- comment -%} inside snippets/price.liquid {%- endcomment -%}
<span class="visually-hidden">{{ 'products.product.price.regular_price' | t }}</span>
```

### Interpolation (named variables)

Define placeholders in the value, pass them as filter arguments:

```json
{
  "cart": {
    "general": {
      "items_count": "You have {{ count }} items in your cart",
      "shipping_to": "Shipping to {{ country }}"
    }
  }
}
```

```liquid
{{ 'cart.general.shipping_to' | t: country: localization.country.name }}
```

### Pluralization

Shopify's `t` filter reads a `count` argument and selects the matching plural form. Supply the CLDR plural categories your locale needs (`zero`, `one`, `two`, `few`, `many`, `other`). English needs `one` + `other`; Arabic needs **all six**.

```json
{
  "cart": {
    "general": {
      "items_count": {
        "one": "{{ count }} item",
        "other": "{{ count }} items"
      }
    }
  }
}
```

```liquid
{{ 'cart.general.items_count' | t: count: cart.item_count }}
```

Arabic (`ar.json`) — Arabic distinguishes all six categories:

```json
{
  "cart": {
    "general": {
      "items_count": {
        "zero": "لا توجد عناصر",
        "one": "عنصر واحد",
        "two": "عنصران",
        "few": "{{ count }} عناصر",
        "many": "{{ count }} عنصرًا",
        "other": "{{ count }} عنصر"
      }
    }
  }
}
```

> If you omit `count`, pluralization silently returns the `other` form. Always pass `count`.

---

## 4. Translating theme-editor settings (schema locale files)

Setting labels, `info`, section names, and select-option labels are **not** hard-coded in the schema. They reference schema-locale keys with the `t:` prefix:

`config/settings_schema.json` (or any `{% schema %}`):

```json
{
  "name": "t:settings_schema.colors.name",
  "settings": [
    {
      "type": "color",
      "id": "color_primary",
      "label": "t:settings_schema.colors.settings.primary.label",
      "info": "t:settings_schema.colors.settings.primary.info"
    }
  ]
}
```

`locales/en.default.schema.json`:

```json
{
  "settings_schema": {
    "colors": {
      "name": "Colors",
      "settings": {
        "primary": {
          "label": "Primary color",
          "info": "Used for buttons and key accents"
        }
      }
    }
  }
}
```

`locales/ar.schema.json`:

```json
{
  "settings_schema": {
    "colors": {
      "name": "الألوان",
      "settings": {
        "primary": {
          "label": "اللون الأساسي",
          "info": "يُستخدم للأزرار واللمسات الرئيسية"
        }
      }
    }
  }
}
```

Rule: **every** `name`, `label`, `info`, and select `option.label` in a schema is a `t:` key. `theme-check` (`SchemaJsonFormat`, `MissingTemplate`) flags raw strings. Default values (`default`) and placeholder-only fields may stay literal.

---

## 5. Setting `<html>` direction in layout/theme.liquid

Direction is derived from the active locale. Shopify exposes `request.locale.iso_code` (e.g. `en`, `ar`) and a curated list of RTL locales. Set both `lang` and `dir` on `<html>`:

```liquid
{%- liquid
  assign rtl_locales = 'ar,he,fa,ur,ps,sd,dv,ug,yi' | split: ','
  assign lang_code = request.locale.iso_code
  assign short_code = lang_code | slice: 0, 2
  assign text_direction = 'ltr'
  if rtl_locales contains short_code
    assign text_direction = 'rtl'
  endif
-%}
<!doctype html>
<html
  lang="{{ request.locale.iso_code }}"
  dir="{{ text_direction }}"
  class="no-js"
>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ content_for_header }}
    {%- comment -%} Expose direction to CSS/JS if needed {%- endcomment -%}
    <script>document.documentElement.classList.remove('no-js');</script>
  </head>
  <body class="dir-{{ text_direction }}">
    {{ content_for_layout }}
  </body>
</html>
```

Now `[dir="rtl"]` and `:dir(rtl)` selectors are available for the rare cases logical properties cannot cover (icon mirroring, transforms).

---

## 6. CSS logical properties — the core of RTL

Replace **every** physical property with its logical equivalent. Logical properties resolve relative to `dir`, so one rule works both ways.

| ❌ Physical (never) | ✅ Logical (always) |
| --- | --- |
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `padding-left` / `padding-right` | `padding-inline-start` / `padding-inline-end` |
| `padding: 0 16px` | `padding-inline: 16px` / `padding-block: 0` |
| `left: 0` | `inset-inline-start: 0` |
| `right: 0` | `inset-inline-end: 0` |
| `text-align: left` | `text-align: start` |
| `text-align: right` | `text-align: end` |
| `border-left` | `border-inline-start` |
| `border-radius: 8px 0 0 8px` | `border-start-start-radius` / `border-end-start-radius` |
| `float: left` | avoid float; use flex/grid (see below) |
| `transform: translateX(100%)` (drawer) | direction-aware transform (see §7) |

Example — a card that must indent from the reading-start edge:

```css
.card {
  padding-inline: var(--space-4);
  padding-block: var(--space-3);
  margin-inline-start: var(--space-2);
  border-inline-start: 3px solid var(--color-primary);
  text-align: start;
}
```

### Flex & grid are direction-aware for free

`flex-direction: row` and grid column order already follow `dir`. Do **not** hard-set order with physical assumptions. Use logical gaps (`gap` is direction-neutral) and let the writing mode flip the axis:

```css
.toolbar {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-start; /* start = reading start, flips in RTL */
}
```

Avoid `justify-content: left/right` (physical, not supported the same way) — use `flex-start` / `flex-end` / `start` / `end`.

---

## 7. Mirroring directional UI

Some things must be **actively mirrored**, not just flowed. Handle each:

### Directional icons (chevrons, arrows, back/next)

Flip with a transform under RTL. Icons that are **symbolic and non-directional** (search, cart, heart) must **not** flip.

```css
[dir="rtl"] .icon-directional {
  transform: scaleX(-1);
}
```

Mark directional icons with a class (`icon-directional`) so you never blanket-flip. Never flip logos, brand marks, or media.

### Cart drawer / off-canvas menu (slides from the correct edge)

A drawer that slides in from the reading-end edge must slide from the **right in LTR** and the **left in RTL**. Use logical positioning + a direction-aware transform:

```css
.drawer {
  position: fixed;
  inset-block: 0;
  inset-inline-end: 0;            /* anchored to reading-end edge */
  inline-size: min(90vw, 400px);
  transform: translateX(100%);   /* off-screen toward the end edge */
}
[dir="rtl"] .drawer {
  transform: translateX(-100%);  /* mirror the hide direction */
}
.drawer.is-open {
  transform: translateX(0);
}
```

### Carousels / sliders

- Native scroll carousels: set `direction` via the container's inherited `dir` and use logical scroll — `scroll-snap` respects writing direction. Compute scroll offsets with sign awareness (in RTL, `scrollLeft` is negative or reversed depending on browser; prefer `element.scrollBy({ left: inlineDelta })` and flip `inlineDelta` sign for RTL, or use `scrollIntoView`).
- Prev/next buttons: "next" always advances in reading order. Swap the visual arrow, not the logic. Bind "next" to advance and let icon mirroring (§7) show the correct arrow.

### Breadcrumbs

Separators and order flow reading-start → reading-end automatically if you use inline flow + logical margins. Mirror the separator glyph (`/` or `›`) — a `›` should become `‹` in RTL; use a mirrorable glyph or a flipped icon.

```css
.breadcrumb__separator { margin-inline: var(--space-1); }
[dir="rtl"] .breadcrumb__separator.icon-directional { transform: scaleX(-1); }
```

### Quantity steppers

`[ − ] [ 3 ] [ + ]` must keep − on the reading-start side and + on the reading-end side, and the field between. Because it's a flex row with logical order, it flips automatically — **do not** hard-position the buttons. Verify the − / + don't swap semantics (minus still decrements).

---

## 8. Bidi handling for numbers, prices, and mixed text

Arabic is RTL but Western digits and currency symbols are LTR runs. Without care, `SAR 1,299.00` can render with the symbol on the wrong side or digits reordered.

- Wrap prices and standalone numeric/latin runs in an element with `dir="ltr"` (or `unicode-bidi: isolate`) so the bidi algorithm keeps them intact:

```liquid
<span class="price" dir="ltr">{{ product.price | money }}</span>
```

```css
.price { unicode-bidi: isolate; }
```

- Use `{{ ... | money }}` / `money_with_currency` — never concatenate a hard-coded symbol.
- Phone numbers, SKUs, and order numbers: same treatment (`dir="ltr"` + `unicode-bidi: isolate`).
- For inline mixed content, prefer the Unicode isolate via CSS over injecting control characters.

---

## 9. Arabic-capable font stack (through font settings)

Arabic needs fonts with Arabic glyph coverage. Do not hard-code a Latin-only family. Expose a body and heading `font_picker` setting and provide an Arabic-safe fallback in the token layer:

```css
:root {
  --font-body-family: {{ settings.type_body_font.family }}, {{ settings.type_body_font.fallback_families }};
  --font-heading-family: {{ settings.type_heading_font.family }}, {{ settings.type_heading_font.fallback_families }};
}
[dir="rtl"] {
  /* Prefer an Arabic-capable stack; merchant can override via an Arabic font setting */
  --font-body-family: "Noto Kufi Arabic", "Cairo", {{ settings.type_body_font.fallback_families }}, sans-serif;
  --font-heading-family: "Noto Kufi Arabic", "Cairo", {{ settings.type_heading_font.fallback_families }}, sans-serif;
}
```

Best practice: give the merchant a **dedicated Arabic font setting** (separate `font_picker`) and swap it under `[dir="rtl"]` so Latin and Arabic can be typeset independently. Also expose a line-height token per direction — Arabic often needs slightly more `--line-body` for diacritics.

Line the `@font-face` / font asset preloads in `theme.liquid`; ensure the Arabic font's `unicode-range` covers `U+0600–06FF`.

---

## 10. Full mini example

### `locales/en.default.json`

```json
{
  "general": {
    "search": {
      "search": "Search",
      "placeholder": "Search products…",
      "no_results": "No results for “{{ terms }}”"
    },
    "pagination": {
      "previous": "Previous",
      "next": "Next"
    }
  },
  "products": {
    "product": {
      "add_to_cart": "Add to cart",
      "sold_out": "Sold out",
      "on_sale": "Sale",
      "from_price": "From {{ price }}"
    }
  },
  "cart": {
    "general": {
      "title": "Your cart",
      "empty": "Your cart is empty",
      "subtotal": "Subtotal",
      "items_count": {
        "one": "{{ count }} item",
        "other": "{{ count }} items"
      }
    }
  },
  "accessibility": {
    "skip_to_text": "Skip to content",
    "close": "Close",
    "open_cart": "Open cart drawer"
  }
}
```

### `locales/ar.json`

```json
{
  "general": {
    "search": {
      "search": "بحث",
      "placeholder": "ابحث عن المنتجات…",
      "no_results": "لا توجد نتائج لـ ”{{ terms }}“"
    },
    "pagination": {
      "previous": "السابق",
      "next": "التالي"
    }
  },
  "products": {
    "product": {
      "add_to_cart": "أضف إلى السلة",
      "sold_out": "نفد المخزون",
      "on_sale": "تخفيض",
      "from_price": "ابتداءً من {{ price }}"
    }
  },
  "cart": {
    "general": {
      "title": "سلة التسوق",
      "empty": "سلة التسوق فارغة",
      "subtotal": "المجموع الفرعي",
      "items_count": {
        "zero": "لا توجد عناصر",
        "one": "عنصر واحد",
        "two": "عنصران",
        "few": "{{ count }} عناصر",
        "many": "{{ count }} عنصرًا",
        "other": "{{ count }} عنصر"
      }
    }
  },
  "accessibility": {
    "skip_to_text": "تخطَّ إلى المحتوى",
    "close": "إغلاق",
    "open_cart": "افتح سلة التسوق"
  }
}
```

Note: keys are byte-for-byte identical; only values differ. `ar.json` adds extra plural categories to `items_count`, which is allowed (English simply never selects them).

---

## 11. RTL audit checklist

Run this before shipping any section/template. Every box must be checked in **both** LTR and an RTL locale preview.

- [ ] `<html dir>` flips to `rtl` on Arabic (verify in DOM), `lang` matches locale.
- [ ] **Zero** physical directions in CSS — grep the stylesheet for `left`, `right`, `margin-left`, `padding-right`, `text-align: left|right`, `float`. All replaced with logical properties.
- [ ] Every layout mirrors: paddings, indents, borders, alignment all swap sides in RTL.
- [ ] Flex/grid rows reverse reading order correctly; no `justify-content: left/right`.
- [ ] Directional icons (chevrons, arrows, back/next, breadcrumb separators) are flipped via `[dir="rtl"] .icon-directional { transform: scaleX(-1); }`; symbolic icons (search, cart, logo, media) are **not** flipped.
- [ ] Cart drawer / off-canvas menu slides in from the correct edge (right in LTR, left in RTL).
- [ ] Carousel prev/next advance in reading order; scroll offset sign handled for RTL.
- [ ] Quantity stepper: minus on reading-start, plus on reading-end, semantics intact.
- [ ] Prices, phone numbers, SKUs wrapped `dir="ltr"` + `unicode-bidi: isolate`; symbol on correct side; digits not reordered.
- [ ] Arabic font stack applied under `[dir="rtl"]`; glyphs render (no tofu boxes); line-height comfortable for diacritics.
- [ ] **No hard-coded strings** anywhere — every visible string, aria-label, placeholder, and empty-state routes through a `t` key present in all locale files.
- [ ] Every schema `name` / `label` / `info` / option label is a `t:` schema key; `en.default.schema.json` + `ar.schema.json` both complete.
- [ ] `theme-check` passes with no `TranslationKeyExists` / `MissingTemplate` / schema-format warnings.
- [ ] Pluralized strings pass `count`; Arabic supplies all six CLDR plural forms it needs.
