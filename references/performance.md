# Performance: Core Web Vitals for Shopify Themes

Theme Store and merchants judge themes on speed. Build to hit these targets on a mid-tier mobile
device on a throttled connection, measured on real templates (home, collection, product).

## Core Web Vitals targets

| Metric | Target ("good") | What it measures | Primary levers |
|--------|-----------------|------------------|----------------|
| **LCP** | < 2.5s | Largest content paint (usually hero image / product image) | image priority, preload, sizing, no render-blocking |
| **CLS** | < 0.1 | Layout shift | explicit width/height, aspect-ratio boxes, reserved space, font-display swap |
| **INP** | < 200ms | Interaction responsiveness | small/deferred JS, event delegation, no long tasks, passive listeners |

Also watch: **TTFB** (Liquid render time — avoid N+1), **TBT/Total JS**, and asset weight.

---

## 1. Images (the #1 lever)

Use Shopify's responsive image helpers everywhere. Never a bare `<img src="{{ image | img_url }}">`.

```liquid
{%- comment -%} snippets/responsive-image.liquid {%- endcomment -%}
<img
  src="{{ image | image_url: width: 800 }}"
  srcset="
    {{ image | image_url: width: 400 }} 400w,
    {{ image | image_url: width: 800 }} 800w,
    {{ image | image_url: width: 1200 }} 1200w,
    {{ image | image_url: width: 1600 }} 1600w"
  sizes="{{ sizes | default: '(min-width: 750px) 50vw, 100vw' }}"
  width="{{ image.width }}"
  height="{{ image.height }}"
  alt="{{ image.alt | escape }}"
  loading="{{ loading | default: 'lazy' }}"
  {% if fetch_priority %}fetchpriority="{{ fetch_priority }}"{% endif %}>
```

Rules:
- **`width`/`height`** always set (real intrinsic dimensions) → browser reserves space → no CLS.
  Combine with an aspect-ratio box for art-directed crops.
- **`srcset` + `sizes`**: give real candidate widths and an accurate `sizes` that matches layout.
  Don't ship a 1600px image into a 400px slot.
- **`loading="lazy"`** for everything below the fold. **`loading="eager"`** (or omit) for the
  LCP element — never lazy-load the hero/first product image.
- **`fetchpriority="high"`** on the single LCP image so the browser fetches it first.
- **Preload** the LCP hero in `<head>` (see below).
- **Modern formats**: Shopify CDN auto-negotiates WebP/AVIF via `image_url` — don't force format.
- **Don't oversize**: cap `image_url` widths to what the layout can display (retina = 2×).

**Aspect-ratio box to kill CLS on responsive crops:**
```css
.media { position: relative; aspect-ratio: var(--ratio, 1); overflow: hidden; }
.media img { width: 100%; height: 100%; object-fit: cover; }
```
```liquid
<div class="media" style="--ratio: {{ section.settings.image.aspect_ratio | default: 1 }};">
```

**Preload the LCP hero** (only the one that is actually the LCP on that template):
```liquid
{%- if template == 'index' and section.settings.image != blank -%}
  <link rel="preload" as="image"
        href="{{ section.settings.image | image_url: width: 1600 }}"
        imagesrcset="{{ section.settings.image | image_url: width: 800 }} 800w,
                     {{ section.settings.image | image_url: width: 1600 }} 1600w"
        imagesizes="100vw" fetchpriority="high">
{%- endif -%}
```

---

## 2. CSS

- **Avoid render-blocking CSS.** Prefer per-section `{% stylesheet %}` blocks (Shopify bundles
  and defers them) and scoped rules over a giant global `theme.css` in the critical path.
- **Inline critical CSS** for above-the-fold (base tokens via `css-variables.liquid`'s
  `{% style %}`, layout skeleton) directly in `<head>`.
- **Minimize** shipped CSS; delete dead rules. `{% stylesheet %}` blocks are minified for you.
- **No `@import`** in CSS — it serializes downloads. Use `{% stylesheet %}`/asset tags.
- **`contain: layout` / `content-visibility: auto`** on below-the-fold sections to skip
  offscreen layout/paint:
  ```css
  .section--deferred { content-visibility: auto; contain-intrinsic-size: auto 600px; }
  ```
- Reference tokens only (see `design-tokens.md`) — keeps CSS small and consistent.

---

## 3. JavaScript

- **`type="module"` + defer semantics.** Module scripts are deferred by default. Load with
  `<script src="{{ 'x.js' | asset_url }}" type="module"></script>` — never blocking `<head>` JS.
- **Custom elements per section** — self-contained, upgrade only when present. Code-split: each
  section ships only the JS it needs; don't load PDP gallery JS on the homepage.
- **Event delegation** — one listener on a container, not one per card.
- **No jQuery / no heavy frameworks.** Vanilla ES modules only.
- **Avoid layout thrash** — batch DOM reads then writes; use `requestAnimationFrame` for
  animation-driven changes; cache `getBoundingClientRect` results.
- **Passive listeners** for scroll/touch: `addEventListener('scroll', fn, { passive: true })`.
- **IntersectionObserver** for lazy behaviors (reveal-on-scroll, deferred section hydration,
  lazy media) instead of scroll handlers.
- **Keep main-thread tasks < 50ms.** Break up work; defer non-critical init to `requestIdleCallback`.
- Debounce/throttle input handlers (search-as-you-type, resize).

---

## 4. Fonts

- Use `font_face` from the theme font object with **`font_display: 'swap'`** (see
  `design-tokens.md`) — text shows immediately in fallback, swaps when the web font loads → no
  invisible-text delay, less CLS.
- **Preconnect** to the Shopify font CDN early:
  ```liquid
  <link rel="preconnect" href="https://fonts.shopifycdn.com" crossorigin>
  ```
- **Limit families & weights.** Two families max (heading + body). Derive bold via `font_modify`
  rather than loading many weights. Every extra weight is a download.
- Prefer Shopify's font library (served from its CDN, subset) over self-hosting arbitrary fonts.
- Choose a fallback family whose metrics are close to the web font to minimize swap shift.

---

## 5. Third-party & app scripts

- **Defer everything non-critical.** Add `defer`/`async`; never let an app tag block render.
- **Facade pattern** for heavy embeds (YouTube/Vimeo, chat widgets, maps): render a lightweight
  placeholder (poster image + play button) and only load the real embed on interaction.
  ```html
  <lite-youtube data-id="{{ block.settings.video_id }}"><button>Play</button></lite-youtube>
  ```
- Audit app-injected scripts; each one costs INP/TBT. Remove unused apps' leftover script tags.
- Load analytics/pixels after load or via `requestIdleCallback`.
- `rel="preconnect"`/`dns-prefetch` only for domains you'll definitely use.

---

## 6. Liquid render performance (TTFB)

- **Avoid N+1 loops.** Don't loop products then access `product.variants`/`.metafields`/
  `.images` in ways that re-query. Assign once, reuse.
- **Cap loop sizes** — paginate collections (`paginate` tag), limit `for` with `limit:`.
- Don't render hidden markup for every product "just in case"; render on demand
  (e.g. quick-add markup only when the feature is on).
- Use `{%- -%}` whitespace control and keep sections lean; heavy Liquid = slow server render.
- Cache-friendly: keep per-request Liquid logic minimal.

---

## 7. Section-level lazy rendering & prefetch

- **Defer offscreen sections** with `content-visibility: auto` (above) and/or hydrate their JS
  via IntersectionObserver only when scrolled near.
- **Prefetch on hover/focus** for product cards → snappier PDP navigation:
  ```js
  card.addEventListener('pointerenter', () => {
    const l = document.createElement('link');
    l.rel = 'prefetch'; l.href = card.dataset.url; l.as = 'document';
    document.head.appendChild(l);
  }, { once: true, passive: true });
  ```
- Consider `<link rel="prefetch">` for the first collection's PDP from the homepage.

---

## 8. CWV budget table

| Resource / metric | Budget (per template) |
|-------------------|----------------------|
| LCP | < 2.5s (target ~2.0s) |
| CLS | < 0.1 |
| INP | < 200ms |
| Total JS (compressed) | < 100 KB critical, < 300 KB total |
| Total CSS (compressed) | < 50 KB critical path |
| Largest image (delivered) | ≤ display size × 2 (retina); hero ≤ ~200 KB |
| Web fonts | ≤ 2 families, ≤ 4 files |
| Third-party requests | minimize; each justified |
| Main-thread long tasks | none > 50ms during load |

---

## 9. Performance checklist

**Images**
- [ ] All images use `image_url` + `srcset` + accurate `sizes` + intrinsic `width`/`height`.
- [ ] Below-fold `loading="lazy"`; LCP image eager + `fetchpriority="high"` + preloaded.
- [ ] Aspect-ratio boxes on all responsive/cropped media (zero CLS).
- [ ] No oversized images; CDN auto-format (no forced format).

**CSS**
- [ ] Critical CSS inline; no render-blocking global stylesheet; no `@import`.
- [ ] Per-section `{% stylesheet %}`; `content-visibility`/`contain` on deferred sections.
- [ ] References tokens only; dead CSS removed.

**JS**
- [ ] `type="module"`, deferred; custom elements; code-split per section.
- [ ] Event delegation, passive listeners, IntersectionObserver for lazy work.
- [ ] No jQuery; no long tasks > 50ms; input handlers throttled.

**Fonts**
- [ ] `font_face` + `font-display: swap`; preconnect to font CDN; ≤ 2 families; bold via `font_modify`.

**Third-party**
- [ ] All non-critical scripts deferred; facades for heavy embeds; analytics idle-loaded.

**Liquid**
- [ ] No N+1 loops; collections paginated; loops limited; whitespace controlled.

**Navigation**
- [ ] Prefetch-on-hover for product cards; deferred offscreen section hydration.

**Verification & theme-check**
- [ ] `theme-check` passes, including **asset-size checks** (`AssetSizeCSS`, `AssetSizeJavaScript`,
      `AssetSizeCSSStylesheetTag`, `RemoteAsset`, `ImgWidthAndHeight`, `ImgLazyLoading`).
- [ ] Lighthouse mobile: Performance ≥ 90, real-template CWV all green.
- [ ] Re-measured after adding sections/apps — perf is a moving target.
