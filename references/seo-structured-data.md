# SEO + Structured Data

This is your reference for making the theme technically discoverable: correct semantic markup, complete meta/Open Graph/Twitter tags, valid JSON-LD schema.org structured data, canonical + hreflang handling, and clean pagination. Everything reads **real Shopify objects** (`product`, `collection`, `article`, `shop`, `blog`, `paginate`) so the merchant never edits code to get correct SEO.

Guiding rules:

- **One `<h1>` per page.** Headings descend logically (`h1 → h2 → h3`), never skip levels for styling — style with CSS/tokens, not heading level.
- **All structured data reads live objects.** Never hard-code price, availability, or title. Wrong/stale JSON-LD triggers Google rich-result penalties.
- **Escape everything** going into JSON-LD with `| json` (handles quotes, newlines, unicode). Never string-concatenate JSON.
- **Every image has meaningful `alt`** sourced from the media/object, not a filename.

---

## 1. Meta tags snippet — `snippets/meta-tags.liquid`

Render once from `<head>` in `layout/theme.liquid`. It derives title, description, canonical, Open Graph, and Twitter card from real objects, with sensible fallbacks to shop-level settings.

```liquid
{%- comment -%}
  snippets/meta-tags.liquid
  Renders <title>, description, canonical, Open Graph, Twitter card.
  Reads: page_title, page_description, canonical_url, request, shop, and
  template-specific objects (product / collection / article) via `template`.
{%- endcomment -%}

<title>
  {{ page_title }}
  {%- if current_tags %} &ndash; {{ 'general.meta.tags' | t: tags: current_tags | join: ', ' }}{% endif -%}
  {%- if current_page != 1 %} &ndash; {{ 'general.meta.page' | t: page: current_page }}{% endif -%}
  {%- unless page_title contains shop.name %} &ndash; {{ shop.name }}{% endunless -%}
</title>

{%- if page_description -%}
  <meta name="description" content="{{ page_description | escape }}">
{%- endif -%}

{%- comment -%} Canonical — Shopify computes the correct canonical URL {%- endcomment -%}
<link rel="canonical" href="{{ canonical_url }}">

{%- comment -%} Robots: noindex thin/utility pages {%- endcomment -%}
{%- if template contains 'cart' or template contains 'customers' or template == 'gift_card' -%}
  <meta name="robots" content="noindex, nofollow">
{%- endif -%}

{%- comment -%} ---- Open Graph ---- {%- endcomment -%}
<meta property="og:site_name" content="{{ shop.name }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:title" content="{{ page_title | escape }}">
{%- if page_description -%}
  <meta property="og:description" content="{{ page_description | escape }}">
{%- endif -%}

{%- liquid
  case template.name
    when 'product'
      assign og_type = 'product'
      assign og_image = product.selected_or_first_available_variant.image | default: product.featured_media.preview_image
    when 'article'
      assign og_type = 'article'
      assign og_image = article.image
    else
      assign og_type = 'website'
      assign og_image = page_image | default: settings.share_image
  endcase
-%}
<meta property="og:type" content="{{ og_type }}">

{%- if og_image -%}
  <meta property="og:image" content="https:{{ og_image | image_url: width: 1200 }}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="{{ 1200 | divided_by: og_image.aspect_ratio | round }}">
  <meta property="og:image:alt" content="{{ og_image.alt | default: page_title | escape }}">
{%- endif -%}

{%- comment -%} ---- Twitter Card ---- {%- endcomment -%}
<meta name="twitter:card" content="summary_large_image">
{%- if settings.social_twitter_handle -%}
  <meta name="twitter:site" content="@{{ settings.social_twitter_handle }}">
{%- endif -%}
<meta name="twitter:title" content="{{ page_title | escape }}">
{%- if page_description -%}
  <meta name="twitter:description" content="{{ page_description | escape }}">
{%- endif -%}
{%- if og_image -%}
  <meta name="twitter:image" content="https:{{ og_image | image_url: width: 1200 }}">
{%- endif -%}
```

Notes:

- `page_title`, `page_description`, and `canonical_url` are **global objects** Shopify populates from the current resource (product/collection/article/page) or its SEO fields — you don't compute them.
- Merchant SEO overrides (title/description set in admin) flow into these automatically.
- Provide `settings.share_image` (image_picker) + `settings.social_twitter_handle` (text) so the merchant controls fallbacks with no code.

---

## 2. Pagination `rel` — `snippets/pagination-rel.liquid`

Emit `rel="prev"`/`rel="next"` in `<head>` for paginated collection/blog/search pages so crawlers understand the series. Requires the resource is wrapped in `{% paginate %}` and you pass the `paginate` object.

```liquid
{%- comment -%} render from head: {% render 'pagination-rel', paginate: paginate %} {%- endcomment -%}
{%- if paginate.previous -%}
  <link rel="prev" href="{{ paginate.previous.url }}">
{%- endif -%}
{%- if paginate.next -%}
  <link rel="next" href="{{ paginate.next.url }}">
{%- endif -%}
```

---

## 3. hreflang for multi-locale / multi-market — `snippets/hreflang.liquid`

Tell search engines about alternate-language / alternate-market versions of the current URL. Shopify exposes `localization.available_languages` and each language's `root_url`.

```liquid
{%- comment -%} snippets/hreflang.liquid — render from <head> {%- endcomment -%}
{%- if localization.available_languages.size > 1 -%}
  {%- for language in localization.available_languages -%}
    <link
      rel="alternate"
      hreflang="{{ language.iso_code }}"
      href="{{ request.origin }}{{ language.root_url }}{{ request.path | remove_first: localization.language.root_url | prepend: '/' | replace: '//', '/' }}{{ request.path == '/' | ternary: '', '' }}"
    >
  {%- endfor -%}
  <link rel="alternate" hreflang="x-default" href="{{ request.origin }}{{ request.path }}">
{%- endif -%}
```

> Practical simpler form Shopify recommends: emit one `<link rel="alternate" hreflang>` per available language pointing at that language's `root_url`-prefixed path. Keep `x-default` for the primary market. Validate paths don't double-prefix the locale root.

---

## 4. JSON-LD: Product — `snippets/schema-product.liquid`

Include on the product template. Reads offers, price, availability, brand, sku, gtin, and aggregate rating (from a reviews metafield when present).

```liquid
{%- comment -%} snippets/schema-product.liquid — pass product {%- endcomment -%}
{%- liquid
  assign current_variant = product.selected_or_first_available_variant
  assign product_image = current_variant.image | default: product.featured_media.preview_image
-%}
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": {{ product.title | json }},
  "url": {{ shop.url | append: product.url | json }},
  "description": {{ product.description | strip_html | truncate: 500 | json }},
  {% if product_image %}"image": [{{ product_image | image_url: width: 1200 | prepend: 'https:' | json }}],{% endif %}
  {% if product.vendor != blank %}"brand": { "@type": "Brand", "name": {{ product.vendor | json }} },{% endif %}
  {% if current_variant.sku != blank %}"sku": {{ current_variant.sku | json }},{% endif %}
  {% if current_variant.barcode != blank %}"gtin": {{ current_variant.barcode | json }},{% endif %}
  {%- comment -%} aggregateRating from a reviews metafield if the app writes one {%- endcomment -%}
  {%- assign rating = product.metafields.reviews.rating.value -%}
  {%- assign rating_count = product.metafields.reviews.rating_count -%}
  {% if rating and rating_count and rating_count > 0 %}
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": {{ rating.rating | json }},
    "bestRating": {{ rating.scale_max | json }},
    "ratingCount": {{ rating_count | json }}
  },
  {% endif %}
  "offers": [
    {%- for variant in product.variants -%}
    {
      "@type": "Offer",
      {% if variant.sku != blank %}"sku": {{ variant.sku | json }},{% endif %}
      "url": {{ shop.url | append: product.url | append: '?variant=' | append: variant.id | json }},
      "price": {{ variant.price | divided_by: 100.0 | json }},
      "priceCurrency": {{ cart.currency.iso_code | json }},
      "availability": "https://schema.org/{% if variant.available %}InStock{% else %}OutOfStock{% endif %}",
      "itemCondition": "https://schema.org/NewCondition"
    }{%- unless forloop.last -%},{%- endunless -%}
    {%- endfor -%}
  ]
}
</script>
```

Notes:

- `price` must be a **decimal in the store currency** — divide the cents integer by `100.0`.
- `gtin` maps to `variant.barcode` when it's a real GTIN/UPC/EAN; if barcodes are arbitrary, omit it.
- Only emit `aggregateRating` when a real review count exists — fabricated ratings are a policy violation.
- Validate with Google Rich Results Test after wiring.

---

## 5. JSON-LD: BreadcrumbList — `snippets/schema-breadcrumb.liquid`

```liquid
{%- comment -%} snippets/schema-breadcrumb.liquid {%- endcomment -%}
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": {{ 'general.breadcrumbs.home' | t | json }},
      "item": {{ shop.url | json }}
    }
    {%- if template contains 'product' -%}
      {%- if collection.url -%},
      {
        "@type": "ListItem",
        "position": 2,
        "name": {{ collection.title | json }},
        "item": {{ shop.url | append: collection.url | json }}
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": {{ product.title | json }},
        "item": {{ shop.url | append: product.url | json }}
      }
      {%- else -%},
      {
        "@type": "ListItem",
        "position": 2,
        "name": {{ product.title | json }},
        "item": {{ shop.url | append: product.url | json }}
      }
      {%- endif -%}
    {%- elsif template contains 'collection' and collection -%},
      {
        "@type": "ListItem",
        "position": 2,
        "name": {{ collection.title | json }},
        "item": {{ shop.url | append: collection.url | json }}
      }
    {%- elsif template contains 'article' and article -%},
      {
        "@type": "ListItem",
        "position": 2,
        "name": {{ blog.title | json }},
        "item": {{ shop.url | append: blog.url | json }}
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": {{ article.title | json }},
        "item": {{ shop.url | append: article.url | json }}
      }
    {%- endif -%}
  ]
}
</script>
```

---

## 6. JSON-LD: Organization + WebSite (with Sitelinks Searchbox) — `snippets/schema-website.liquid`

Include on the **homepage only** (`template.name == 'index'`). `WebSite` + `potentialAction` enables the Google sitelinks search box; `Organization` feeds the knowledge panel.

```liquid
{%- comment -%} snippets/schema-website.liquid — homepage only {%- endcomment -%}
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Organization",
  "name": {{ shop.name | json }},
  "url": {{ shop.url | json }},
  {% if settings.logo %}"logo": {{ settings.logo | image_url: width: 500 | prepend: 'https:' | json }},{% endif %}
  {%- assign socials = '' | split: '' -%}
  {%- if settings.social_instagram_link != blank %}{% assign socials = socials | concat: settings.social_instagram_link | split: '¦¦' | first | split: '' %}{% endif -%}
  "sameAs": [
    {%- assign s_list = '' -%}
    {%- if settings.social_facebook_link != blank %}{{ settings.social_facebook_link | json }}{% assign s_list = 'y' %}{% endif -%}
    {%- if settings.social_instagram_link != blank %}{% if s_list == 'y' %},{% endif %}{{ settings.social_instagram_link | json }}{% assign s_list = 'y' %}{% endif -%}
    {%- if settings.social_tiktok_link != blank %}{% if s_list == 'y' %},{% endif %}{{ settings.social_tiktok_link | json }}{% endif -%}
  ]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "WebSite",
  "name": {{ shop.name | json }},
  "url": {{ shop.url | json }},
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": {{ shop.url | append: '/search?q={search_term_string}' | json }}
    },
    "query-input": "required name=search_term_string"
  }
}
</script>
```

> Keep `sameAs` simple — provide social link settings and list only non-blank ones. The verbose concat above is illustrative; in practice build the array by pushing non-blank settings.

---

## 7. JSON-LD: Article / BlogPosting — `snippets/schema-article.liquid`

```liquid
{%- comment -%} snippets/schema-article.liquid — pass article, blog {%- endcomment -%}
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "BlogPosting",
  "mainEntityOfPage": { "@type": "WebPage", "@id": {{ shop.url | append: article.url | json }} },
  "headline": {{ article.title | json }},
  {% if article.image %}"image": [{{ article.image | image_url: width: 1200 | prepend: 'https:' | json }}],{% endif %}
  "datePublished": {{ article.published_at | date: '%Y-%m-%dT%H:%M:%SZ' | json }},
  "dateModified": {{ article.updated_at | date: '%Y-%m-%dT%H:%M:%SZ' | json }},
  "author": { "@type": "Person", "name": {{ article.author | json }} },
  "publisher": {
    "@type": "Organization",
    "name": {{ shop.name | json }}
    {% if settings.logo %},"logo": { "@type": "ImageObject", "url": {{ settings.logo | image_url: width: 500 | prepend: 'https:' | json }} }{% endif %}
  },
  "description": {{ article.excerpt_or_content | strip_html | truncate: 300 | json }}
}
</script>
```

---

## 8. JSON-LD: ItemList for collections — `snippets/schema-collection.liquid`

Lists the products on a collection page in order. Cap at a reasonable count (e.g. first page) to keep payload small.

```liquid
{%- comment -%} snippets/schema-collection.liquid — pass collection {%- endcomment -%}
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "ItemList",
  "name": {{ collection.title | json }},
  "itemListElement": [
    {%- for product in collection.products limit: 24 -%}
    {
      "@type": "ListItem",
      "position": {{ forloop.index }},
      "url": {{ shop.url | append: product.url | json }},
      "name": {{ product.title | json }}
    }{%- unless forloop.last -%},{%- endunless -%}
    {%- endfor -%}
  ]
}
</script>
```

---

## 9. Semantic markup + image alt

- Use landmark elements: `<header>`, `<nav>`, `<main>` (exactly one, wraps `content_for_layout`'s main region), `<footer>`, `<article>`, `<section>` with an accessible name.
- **One `<h1>`** per page — product title on PDP, collection title on PLP, article title on article, shop tagline/hero heading on home. Section headings are `<h2>`.
- Images: always render `alt` from the media object; fall back to a meaningful default, never a filename.

```liquid
{{ image | image_url: width: 800 | image_tag:
  loading: 'lazy',
  widths: '400, 800, 1200',
  alt: image.alt | default: product.title | escape
}}
```

- Above-the-fold hero/first product image: `loading: 'eager'` + `fetchpriority: 'high'`; everything else `loading: 'lazy'`.
- Provide responsive `srcset`/`widths` and `sizes` so crawlers and users get right-sized images (Core Web Vitals = ranking factor).

---

## 10. Wiring it up in `layout/theme.liquid`

```liquid
<head>
  {% render 'meta-tags' %}
  {% if template.name == 'index' %}{% render 'schema-website' %}{% endif %}
  {{ content_for_header }}
</head>
```

And within templates (via sections/snippets), conditionally include the matching JSON-LD:

```liquid
{% render 'schema-product', product: product %}
{% render 'schema-breadcrumb' %}
{% render 'schema-collection', collection: collection %}
{% render 'schema-article', article: article, blog: blog %}
{% render 'pagination-rel', paginate: paginate %}
{% render 'hreflang' %}
```

---

## 11. SEO checklist

- [ ] Exactly one `<h1>` per page; heading levels descend without skips (styled via tokens, not level).
- [ ] `<title>` derived from `page_title` + shop name; unique per page; page number appended on paginated pages.
- [ ] `<meta name="description">` from `page_description` (merchant-overridable); present on all indexable pages.
- [ ] `<link rel="canonical" href="{{ canonical_url }}">` on every page.
- [ ] `robots` `noindex` on cart, account, gift_card, and other utility/thin pages.
- [ ] Open Graph (`og:title/description/url/type/image` + dimensions + alt) and Twitter card (`summary_large_image`) present; `og:image` from featured media with shop-setting fallback.
- [ ] hreflang alternates emitted for each available language + `x-default`; no double-prefixed locale paths.
- [ ] `rel="prev"`/`rel="next"` on paginated collection/blog/search pages.
- [ ] Product JSON-LD: valid `offers` with decimal `price`, `priceCurrency`, `availability`, `sku`, `brand`; `gtin` only when barcode is a real GTIN; `aggregateRating` only when a real review count exists.
- [ ] BreadcrumbList JSON-LD matches on-page breadcrumb trail.
- [ ] Organization + WebSite (with SearchAction sitelinks searchbox) JSON-LD on homepage only.
- [ ] Article/BlogPosting JSON-LD on articles; ItemList on collections.
- [ ] All JSON-LD escaped via `| json`; validates in Google Rich Results Test with zero errors.
- [ ] Every image has a meaningful `alt` from the object; hero image `eager` + `fetchpriority=high`, rest `lazy` with responsive `srcset`/`sizes`.
- [ ] `theme-check` passes; no raw/unescaped values in structured data.
