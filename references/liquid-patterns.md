# DRY Liquid Patterns

You write senior-level, DRY Liquid: one source of truth per concern, no repetition, no `theme-check` warnings, no cumulative layout shift, no N+1 loops, and every shopper-facing string translated. This doc is your pattern library. Copy the snippets, follow the rules, and consult the deprecated→modern table before using any tag or filter you're unsure about.

---

## 1. Snippetization: `render`, not `include`

`{% include %}` is deprecated (leaky scope, slow). **Always** use `{% render %}`, which runs in an isolated scope — the snippet sees only the variables you pass plus global objects.

```liquid
{%- comment -%} pass named params {%- endcomment -%}
{% render 'price', product: product, show_compare: true %}

{%- comment -%} render once per item in an array; inside, the var is `item` {%- endcomment -%}
{% render 'card-product' for collection.products as card %}
{%- comment -%} ^ `for ... as card` binds each element to `card` and exposes forloop {%- endcomment -%}

{%- comment -%} render once with a single object bound to the snippet name {%- endcomment -%}
{% render 'media' with product.featured_media as media %}
```

Rules:
- Isolated scope means a snippet **cannot** read a caller's local `assign`s — pass everything explicitly. This is a feature (predictability), not a bug.
- Global objects (`product` when on a product page, `settings`, `shop`, `cart`, `routes`, `request`) are still available inside snippets.
- Prefer many small focused snippets over one mega-snippet with a `case`.

---

## 2. Responsive images (the one true pattern)

Goals: sharp on every DPR/breakpoint, **no CLS** (always ship `width`+`height`), correct LCP priority (`loading="eager"` + `fetchpriority="high"` for above-the-fold hero; `loading="lazy"` for everything else), and focal-point-aware cropping.

### `snippets/responsive-image.liquid`

```liquid
{%- comment -%}
  Reusable responsive image.
  Accepts:
    image      (required) an image object (product.featured_image, block.settings.image, etc.)
    sizes      (optional) sizes attribute; default full viewport width
    widths     (optional) comma string of candidate widths; sensible default below
    loading    (optional) 'lazy' (default) or 'eager'
    priority   (optional) true → adds fetchpriority="high" (use for LCP image only)
    class      (optional) extra classes
    crop       (optional) crop mode; focal point is honoured automatically
{%- endcomment -%}

{%- liquid
  assign widths = widths | default: '165, 360, 533, 720, 940, 1066, 1280, 1512, 1728, 2048'
  assign sizes = sizes | default: '100vw'
  assign loading = loading | default: 'lazy'
-%}

{%- if image != blank -%}
  <img
    src="{{ image | image_url: width: 720 }}"
    srcset="
      {%- assign width_list = widths | split: ',' -%}
      {%- for w in width_list -%}
        {%- assign wt = w | strip -%}
        {{ image | image_url: width: wt }} {{ wt }}w{%- unless forloop.last -%},{%- endunless -%}
      {%- endfor -%}
    "
    sizes="{{ sizes }}"
    width="{{ image.width }}"
    height="{{ image.height }}"
    alt="{{ image.alt | escape }}"
    loading="{{ loading }}"
    {%- if priority %} fetchpriority="high"{% endif %}
    {%- if crop %} data-crop="{{ crop }}"{% endif %}
    class="responsive-image {{ class }}"
  >
{%- else -%}
  {{ 'image' | placeholder_svg_tag: 'responsive-image__placeholder' }}
{%- endif -%}
```

Call sites:

```liquid
{%- comment -%} LCP hero — eager + high priority, spans viewport {%- endcomment -%}
{% render 'responsive-image', image: section.settings.hero, loading: 'eager', priority: true, sizes: '100vw' %}

{%- comment -%} product card in a 4-col grid — lazy, sized to column {%- endcomment -%}
{% render 'responsive-image', image: card.featured_image,
   sizes: '(min-width: 990px) 25vw, (min-width: 750px) 50vw, 100vw' %}
```

Why each piece:
- `image_url: width: N` — generates a Shopify CDN URL at width N. Never use the legacy `img_url`.
- `srcset` with `Nw` descriptors + `sizes` → the browser picks the right file.
- `width`/`height` from `image.width`/`image.height` set the intrinsic aspect ratio → **zero CLS**.
- Focal point: Shopify's CDN honours the image's focal point automatically when you crop; pass `crop:` (e.g. `center`) via `image_url: width: N, crop: 'center'` if you need a fixed ratio. To hard-crop to a ratio, add `height:` and `crop:` to the `image_url` calls.

### Art direction (`<picture>`)

When mobile and desktop need genuinely different crops/images:

```liquid
<picture>
  <source
    media="(min-width: 750px)"
    srcset="{{ desktop | image_url: width: 1500 }} 1500w, {{ desktop | image_url: width: 3000 }} 3000w"
    sizes="100vw"
    width="{{ desktop.width }}" height="{{ desktop.height }}">
  <source
    media="(max-width: 749px)"
    srcset="{{ mobile | image_url: width: 750 }} 750w, {{ mobile | image_url: width: 1500 }} 1500w"
    sizes="100vw"
    width="{{ mobile.width }}" height="{{ mobile.height }}">
  <img src="{{ desktop | image_url: width: 1500 }}"
       alt="{{ desktop.alt | escape }}" width="{{ desktop.width }}" height="{{ desktop.height }}"
       loading="lazy">
</picture>
```

Use `<picture>` only for real art direction. For same-image-different-sizes, the single `<img srcset sizes>` above is lighter.

---

## 3. Money formatting

Never build currency strings by hand. Use money filters, which respect the store's currency format settings.

```liquid
{{ product.price | money }}                 {%- comment -%} $24.00 {%- endcomment -%}
{{ product.price | money_with_currency }}   {%- comment -%} $24.00 USD {%- endcomment -%}
{{ product.price | money_without_trailing_zeros }}
```

- `product.price` is in cents (integer) — filters convert. Don't divide by 100 yourself.
- Multi-currency / Markets: `cart.currency.iso_code`, `localization.country.currency` are available; the money filters already localize when Markets is on.
- For ranges: `{{ product.price_min | money }}`–`{{ product.price_max | money }}`, guarding with `product.price_varies`.

---

## 4. Translation + pluralization

Every shopper-facing string is a translation key. Two forms:

```liquid
{%- comment -%} in Liquid output {%- endcomment -%}
{{ 'products.product.add_to_cart' | t }}

{%- comment -%} in schema/settings JSON, use the t: shorthand {%- endcomment -%}
"label": "t:sections.featured.heading"
```

Interpolation and pluralization pull from `locales/*.json`:

```json
{
  "products": {
    "product": {
      "stock_count": {
        "one": "{{ count }} item left",
        "other": "{{ count }} items left"
      },
      "vendor_by": "By {{ vendor }}"
    }
  }
}
```

```liquid
{{ 'products.product.stock_count' | t: count: product.selected_variant.inventory_quantity }}
{{ 'products.product.vendor_by' | t: vendor: product.vendor }}
```

- Pass `count:` to trigger the `one`/`other` (and locale-specific `few`/`many`) plural rules automatically.
- Named variables (`vendor:`) interpolate `{{ vendor }}` placeholders.
- Never concatenate translated fragments — put the whole sentence in the locale file with interpolation.

---

## 5. Settings access

```liquid
{{ settings.logo }}                          {%- comment -%} global theme settings {%- endcomment -%}
{{ section.settings.heading }}               {%- comment -%} this section instance {%- endcomment -%}
{{ block.settings.link }}                     {%- comment -%} a block instance {%- endcomment -%}
```

Guard and default:

```liquid
{%- assign heading = section.settings.heading | default: '' -%}
{%- if section.settings.image != blank -%} ... {%- endif -%}
```

For `checkbox`/`boolean` settings just test truthiness: `{%- if section.settings.show_vendor -%}`.

---

## 6. Loops: `forloop`, and guarding

```liquid
{%- for block in section.blocks -%}
  <li class="{% if forloop.first %}is-first{% endif %}"
      {{ block.shopify_attributes }}>
    {{ forloop.index }} / {{ forloop.length }}
    {{ block.settings.label }}
  </li>
{%- else -%}
  {%- comment -%} runs when the collection is empty {%- endcomment -%}
  <li>{{ 'general.empty' | t }}</li>
{%- endfor -%}
```

Useful `forloop` members: `index` (1-based), `index0`, `first`, `last`, `length`, `rindex`. Use `{%- for … -%}` whitespace control to keep output clean.

---

## 7. Pagination

`{% paginate %}` wraps a loop and gives you a `paginate` object. Respect Shopify limits (max `250` per page for products; use a sane page size like 12–24).

```liquid
{%- paginate collection.products by 24 -%}
  <ul class="product-grid">
    {%- for product in collection.products -%}
      <li>{% render 'card-product', card: product %}</li>
    {%- endfor -%}
  </ul>

  {%- if paginate.pages > 1 -%}
    <nav class="pagination" role="navigation" aria-label="{{ 'general.pagination.label' | t }}">
      {%- if paginate.previous -%}
        <a href="{{ paginate.previous.url }}" rel="prev">{{ 'general.pagination.previous' | t }}</a>
      {%- endif -%}
      {%- for part in paginate.parts -%}
        {%- if part.is_link -%}
          <a href="{{ part.url }}">{{ part.title }}</a>
        {%- else -%}
          <span aria-current="page">{{ part.title }}</span>
        {%- endif -%}
      {%- endfor -%}
      {%- if paginate.next -%}
        <a href="{{ paginate.next.url }}" rel="next">{{ 'general.pagination.next' | t }}</a>
      {%- endif -%}
    </nav>
  {%- endif -%}
{%- endpaginate -%}
```

---

## 8. `capture` / `assign` hygiene (avoid `UnusedAssign`)

`theme-check` flags unused assigns and prefers the `{%- liquid -%}` tag for multi-line logic.

```liquid
{%- liquid
  assign img = block.settings.image | default: product.featured_image
  assign has_badge = false
  if product.compare_at_price > product.price
    assign has_badge = true
  endif
-%}
```

- Every `assign` must be used, or `theme-check` warns — delete dead assigns.
- Use `capture` only when you need to build a *string* of markup; prefer `assign` for values.
- Don't `assign` inside a tight loop what you can compute once outside it.

---

## 9. Guarding nil / blank

```liquid
{%- if product.featured_media != blank -%} ... {%- endif -%}
{%- unless section.settings.heading == blank -%} ... {%- endunless -%}
{{ image.alt | escape | default: product.title | escape }}
```

- `blank` catches empty strings, empty arrays, and nil. Prefer `!= blank` over `!= nil` for settings/metafields.
- Always `escape` user/merchant text output into HTML attributes (`alt`, `title`, `aria-label`).

---

## 10. URL & link filters

```liquid
<a href="{{ product.url }}">…</a>
<a href="{{ routes.cart_url }}">{{ 'general.cart' | t }}</a>          {%- comment -%} never hard-code /cart {%- endcomment -%}
{{ product.title | link_to: product.url }}
{{ collection.url | within: collection }}                             {%- comment -%} keeps collection context on product links {%- endcomment -%}
{{ 'option_disabled.svg' | asset_url }}
{{ image | image_url: width: 400 }}
```

Always use `routes.*` (`routes.root_url`, `routes.cart_url`, `routes.search_url`, `routes.account_url`, etc.) instead of literal paths — required for correct locale/subfolder URLs.

---

## 11. Metafields: access & type handling

```liquid
{%- assign mf = product.metafields.custom.ingredients -%}

{%- if mf != blank -%}
  {%- case mf.type -%}
    {%- when 'rich_text_field' -%}
      {{ mf.value }}                              {%- comment -%} outputs sanitized HTML {%- endcomment -%}
    {%- when 'list.single_line_text_field' -%}
      <ul>
        {%- for v in mf.value -%}<li>{{ v | escape }}</li>{%- endfor -%}
      </ul>
    {%- when 'product_reference' -%}
      {%- assign ref = mf.value -%}
      <a href="{{ ref.url }}">{{ ref.title | escape }}</a>
    {%- when 'file_reference' -%}
      {% render 'responsive-image', image: mf.value %}
    {%- when 'boolean' -%}
      {%- if mf.value -%}✓{%- endif -%}
    {%- else -%}
      {{ mf.value | escape }}
  {%- endcase -%}
{%- endif -%}
```

- `.value` is the payload. For `*_reference` and `metaobject_reference`, `.value` is the referenced object (has `.url`, `.title`, fields, etc.).
- For `list.*`, `.value` is an array — iterate it.
- `rich_text_field` `.value` is safe HTML — output raw; do **not** `escape` it. Everything else that is merchant free text → `escape`.
- Always guard `!= blank` so stores without the definition don't error.

---

## 12. Performance-safe Liquid (no N+1)

- **Never** loop `all_products` unbounded, and never do `all_products[handle]` inside a large loop — each lookup is a query. Prefer `collection.products` inside a `{% paginate %}`.
- Avoid nested loops that hit collections/products per iteration (classic N+1). Fetch once, reuse.
- `{% render %}` inside a loop is fine (isolated + fast); heavy `for` over thousands of items is not — paginate.
- Don't call `image_url` more times than needed; capture repeated URLs.
- Prefer `section.blocks` / passed data over re-querying global objects in loops.
- Use `{%- liquid -%}` blocks to keep logic tight and readable, reducing accidental repeated work.

---

## 13. Copy-paste snippet library

### `snippets/icon.liquid`

```liquid
{%- comment -%} {% render 'icon', name: 'cart', size: 20 %} {%- endcomment -%}
{%- liquid
  assign name = name | default: 'circle'
  assign size = size | default: 24
-%}
<svg class="icon icon--{{ name }}" role="presentation" focusable="false"
     width="{{ size }}" height="{{ size }}" viewBox="0 0 24 24"
     fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
  {%- case name -%}
    {%- when 'cart' -%}<path d="M3 3h2l2 12h10l2-8H6"/><circle cx="9" cy="20" r="1"/><circle cx="17" cy="20" r="1"/>
    {%- when 'search' -%}<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>
    {%- else -%}<circle cx="12" cy="12" r="9"/>
  {%- endcase -%}
</svg>
```

### `snippets/price.liquid`

```liquid
{%- comment -%} {% render 'price', product: product, show_compare: true %} {%- endcomment -%}
{%- liquid
  assign target = product | default: variant
  assign price = target.price
  assign compare = target.compare_at_price
  assign on_sale = false
  if compare > price
    assign on_sale = true
  endif
-%}
<div class="price {% if on_sale %}price--on-sale{% endif %}">
  {%- if product.price_varies -%}
    <span class="price__from">{{ 'products.product.price.from' | t }}</span>
  {%- endif -%}
  <span class="price__regular" style="color: rgb(var(--color-{% if on_sale %}sale{% else %}foreground{% endif %}));">
    {{ price | money }}
  </span>
  {%- if on_sale and show_compare -%}
    <s class="price__compare">{{ compare | money }}</s>
    <span class="visually-hidden">{{ 'products.product.price.sale' | t }}</span>
  {%- endif -%}
</div>
```

### `snippets/rating-stars.liquid` (placeholder for app reviews)

```liquid
{%- comment -%}
  Placeholder rating display driven by a metafield (e.g. reviews.rating).
  Real review apps inject their own block via {"type":"@app"}; this renders a
  merchant-entered fallback so nothing is hard-coded.
  {% render 'rating-stars', rating: product.metafields.reviews.rating.value, count: product.metafields.reviews.rating_count.value %}
{%- endcomment -%}
{%- liquid
  assign rating = rating | default: 0 | plus: 0
  assign count = count | default: 0
-%}
{%- if count > 0 -%}
  <div class="rating" role="img"
       aria-label="{{ 'products.product.rating.label' | t: rating: rating, count: count }}">
    {%- for i in (1..5) -%}
      {%- if i <= rating -%}
        <span class="rating__star is-filled" aria-hidden="true">★</span>
      {%- else -%}
        <span class="rating__star" aria-hidden="true">☆</span>
      {%- endif -%}
    {%- endfor -%}
    <span class="rating__count">({{ count }})</span>
  </div>
{%- endif -%}
```

---

## 14. Deprecated → modern reference

| Deprecated | Use instead | Note |
|---|---|---|
| `{% include 'x' %}` | `{% render 'x' %}` | Isolated scope; pass params explicitly |
| `img_url` filter | `image_url` filter | `{{ img \| image_url: width: 800 }}`; supports `crop`, `format` |
| `{{ img \| img_tag }}` | Build `<img>` with `image_url` + `srcset` + `width`/`height` | Or use `image_tag` filter for a quick tag |
| `{% section %}` for chrome | Section groups + `{% sections 'header-group' %}` | Header/footer are editor-controlled groups now |
| Hard-coded `/cart`, `/search`, `/account` | `routes.cart_url`, `routes.search_url`, `routes.account_url` | Locale/subfolder safe |
| `product.featured_image` alone (no dims) | `image_url` + explicit `width`/`height` | Prevents CLS |
| `{{ 'string' }}` literal shopper text | `{{ 'key' \| t }}` / `t:` in schema | Everything translated |
| `money` string built by hand | `money` / `money_with_currency` filters | Respects store format & Markets |
| `{% assign x = … %}` (multi, verbose) | `{%- liquid … -%}` block | Cleaner, `theme-check` friendly |
| `{{ shop.url }}/products/...` | `product.url`, `collection.url`, `routes.*` | Never assemble URLs manually |
| Dividing price by 100 | `money` filter on cents | Filters handle conversion |

When in doubt, do what current Dawn and the official Shopify Liquid reference do. Never reach for a deprecated tag/filter to save a line.
