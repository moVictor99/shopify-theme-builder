# Accessibility: WCAG 2.1 AA for Shopify Themes

Theme Store requires WCAG 2.1 Level AA. Build it in from the start — retrofitting a11y is
painful. This is your working checklist plus copy-paste-ready patterns. Everything here assumes
the token system in `design-tokens.md` (notably `--color-focus`, `--color-foreground`,
`--color-on-primary`).

---

## 1. Semantic landmarks & document structure

One of each landmark per page, in the right order:

```liquid
{%- comment -%} layout/theme.liquid {%- endcomment -%}
<body>
  <a class="skip-to-content-link visually-hidden-focusable" href="#MainContent">
    {{ 'accessibility.skip_to_text' | t }}
  </a>

  <header role="banner">
    <nav aria-label="{{ 'accessibility.primary_navigation' | t }}"> … </nav>
  </header>

  <main id="MainContent" role="main" tabindex="-1">
    {{ content_for_layout }}
  </main>

  <footer role="contentinfo"> … </footer>
</body>
```

- `<main>` gets `id="MainContent"` and `tabindex="-1"` so the skip link can focus it.
- Use ONE `<h1>` per page (usually the section/product title). Never skip heading levels
  (h1 → h2 → h3). Editor content that would break order should use CSS classes for visual size
  (`.h2`, `.h4`) while keeping the correct semantic tag.
- Landmarks: `banner` (header), `main`, `contentinfo` (footer), `navigation` (nav),
  `complementary` (aside), `search` (search form region). Give multiple `<nav>`s distinct
  `aria-label`s.

**Skip link CSS** (visible only on focus):
```css
.skip-to-content-link {
  position: absolute; top: 0; left: 0; z-index: 1000;
  padding: var(--space-3) var(--space-4);
  background: rgb(var(--color-background));
  color: rgb(var(--color-foreground));
  transform: translateY(-100%);
  transition: transform var(--duration-fast) var(--ease);
}
.skip-to-content-link:focus { transform: translateY(0); }
```

---

## 2. ARIA — only where native HTML can't do it

Prefer native elements (`<button>`, `<a>`, `<details>`, `<label>`). Add ARIA only for custom
interactive widgets. Wrong ARIA is worse than none.

| Component | Required ARIA |
|-----------|---------------|
| Menu / disclosure | `aria-expanded`, `aria-controls` on trigger |
| Drawer / modal | `role="dialog"` (or `alertdialog`), `aria-modal="true"`, `aria-label`/`aria-labelledby` |
| Tabs | `role="tablist"` / `tab` / `tabpanel`, `aria-selected`, `aria-controls`, `id` linkage |
| Accordion | Prefer `<details>/<summary>`; else `aria-expanded` + `aria-controls` |
| Carousel | `aria-roledescription="carousel"`, slide `aria-label="n of m"`, live region for auto-advance status, pause control |
| Current page/nav item | `aria-current="page"` |
| Icon-only button | `aria-label` naming the action |
| Toggle state | `aria-pressed` |
| Loading/updating region | `aria-busy="true"` while fetching |

---

## 3. Keyboard operability

Everything clickable must be reachable and operable by keyboard alone. Test with Tab/Shift+Tab/
Enter/Space/Esc/Arrow keys — unplug the mouse.

- **Never** put click handlers on `<div>`/`<span>`. Use `<button>`/`<a>`. If you truly must,
  add `role`, `tabindex="0"`, and Enter/Space handlers — but don't.
- **Focus trap** in open drawers/modals: Tab cycles within, Shift+Tab from first wraps to last.
- **ESC** closes any drawer/modal/dropdown.
- **Focus return:** store the trigger element on open; `.focus()` it on close.
- **Move focus in** on open: focus the dialog or its first focusable element.
- **Roving tabindex** for menu bars / toolbars / tablists: only one item has `tabindex="0"`,
  the rest `tabindex="-1"`; Arrow keys move focus.
- Don't trap keyboard focus anywhere except intentional modal traps.

---

## 4. Visible focus states

Keyboard users must always see where focus is. Use `:focus-visible` with the focus token.

```css
:where(a, button, input, select, textarea, summary, [tabindex]):focus-visible {
  outline: 2px solid rgb(var(--color-focus));
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
/* Remove the default ring for mouse users, but ONLY because :focus-visible re-adds it */
:where(a, button, input, select, textarea, summary):focus:not(:focus-visible) {
  outline: none;
}
```

Rule: **never `outline: none` without an equally-visible replacement.** The focus indicator must
meet 3:1 contrast against adjacent colors — `--color-focus` is a dedicated, high-contrast token
for exactly this.

---

## 5. Color contrast — enforced by the token system

WCAG AA thresholds:
- **4.5:1** normal text vs its background.
- **3:1** large text (≥24px, or ≥18.66px bold) and UI components / graphical objects / focus ring.

The token pairings that must hold in **every** color scheme:
- `--color-foreground` on `--color-background` ≥ 4.5:1
- `--color-on-primary` on `--color-primary` ≥ 4.5:1
- `--color-border` on `--color-background` ≥ 3:1 (so borders are perceivable)
- `--color-focus` on `--color-background` ≥ 3:1
- `--color-sale` on `--color-background` ≥ 4.5:1

Add `info` text on the color scheme settings reminding merchants to keep contrast, and set
sensible defaults that already pass. Never convey information by color alone — pair the sale
color with the word "Sale"/a badge, pair validation color with an icon + text.

---

## 6. Forms

```liquid
<div class="field">
  <label for="ContactEmail">{{ 'templates.contact.form.email' | t }}</label>
  <input
    type="email" id="ContactEmail" name="contact[email]"
    autocomplete="email" required
    {% if form.errors contains 'email' %}
      aria-invalid="true" aria-describedby="ContactEmail-error"
    {% endif %}>
  {%- if form.errors contains 'email' -%}
    <p id="ContactEmail-error" class="field__error" role="alert">
      <span class="visually-hidden">{{ 'accessibility.error' | t }}:</span>
      {{ form.errors.messages['email'] }}
    </p>
  {%- endif -%}
</div>
```

- Every input has an associated `<label for>` (or `aria-label` for search). Placeholders are
  NOT labels.
- Errors: `aria-invalid="true"` + `aria-describedby` pointing at the message; message has
  `role="alert"` so it's announced.
- Use correct `type` and `autocomplete` tokens (`email`, `name`, `tel`, `street-address`…).
- Group related controls with `<fieldset>`/`<legend>` (e.g. variant radio options).
- Don't disable submit based on JS alone; provide error feedback.

---

## 7. Images & media

- Product/collection images: `alt="{{ image.alt | escape }}"`. Merchant-provided alt text flows
  from Shopify admin — never invent alt in code; use the `alt` field and `escape` it.
- Section image settings: add a companion text/`inline_richtext` setting or use the image's alt.
- **Decorative** images (background flourishes): `alt=""` (empty, present) so SR skips them.
- SVG icons: `aria-hidden="true"` when decorative; wrap actionable icons in a labeled `<button>`.
- Videos: provide captions; don't autoplay with sound; respect reduced motion for autoplay video.

---

## 8. Reduced motion

Honor `prefers-reduced-motion` AND the theme's `animations_enabled` toggle (both collapse
durations to `0ms` via tokens — see `design-tokens.md`). Additionally:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
No parallax, auto-advancing carousels, or large motion for reduced-motion users. Carousels must
have a visible pause control regardless.

---

## 9. Screen-reader-only utility

```css
.visually-hidden {
  position: absolute !important;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
  white-space: nowrap; border: 0;
}
/* Variant that becomes visible on focus (e.g. skip link) */
.visually-hidden-focusable:not(:focus):not(:focus-within) {
  position: absolute !important;
  width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
}
```

Use `.visually-hidden` to give context to SR users: "Sale price", "Regular price", quantity
labels, "Search", pagination "Page 2".

---

## 10. Live regions (cart / add-to-cart / async feedback)

Announce asynchronous changes without moving focus:

```liquid
<div id="cart-live-region" class="visually-hidden" role="status" aria-live="polite"></div>
```
```js
document.getElementById('cart-live-region').textContent =
  window.themeStrings.itemAdded; // e.g. "Item added to cart. 3 items."
```

- `aria-live="polite"` for cart counts, "added to cart", filter result counts.
- `aria-live="assertive"` / `role="alert"` only for errors that need immediate attention.
- Cart bubble count: keep a `.visually-hidden` text ("3 items in cart") alongside the number.

---

## 11. Accessible `<details>`/`<summary>` accordion

Native, keyboard-operable, no JS required:

```liquid
<details class="accordion" {% if block.settings.open %}open{% endif %}>
  <summary class="accordion__summary">
    <span>{{ block.settings.heading | escape }}</span>
    {% render 'icon-chevron' %}
  </summary>
  <div class="accordion__content">
    {{ block.settings.content }}
  </div>
</details>
```
```css
.accordion__summary { cursor: pointer; list-style: none; display: flex;
  justify-content: space-between; align-items: center; gap: var(--space-3); }
.accordion__summary::-webkit-details-marker { display: none; }
.accordion[open] .accordion__summary svg { transform: rotate(180deg); }
.accordion__summary svg { transition: transform var(--duration-fast) var(--ease); }
```
`<summary>` is focusable and toggles on Enter/Space for free. The chevron SVG is decorative
(`aria-hidden`).

---

## 12. Keyboard-operable custom-element drawer skeleton

```html
<cart-drawer>
  <button type="button" aria-expanded="false" aria-controls="CartDrawer" data-open>
    {% render 'icon-cart' %}
    <span class="visually-hidden">{{ 'sections.cart.title' | t }}</span>
  </button>

  <div id="CartDrawer" class="drawer" role="dialog" aria-modal="true"
       aria-label="{{ 'sections.cart.title' | t }}" hidden>
    <button type="button" data-close aria-label="{{ 'accessibility.close' | t }}">
      {% render 'icon-close' %}
    </button>
    <div class="drawer__body"> … </div>
  </div>
</cart-drawer>
```
```js
class CartDrawer extends HTMLElement {
  connectedCallback() {
    this.trigger = this.querySelector('[data-open]');
    this.dialog  = this.querySelector('[role="dialog"]');
    this.trigger.addEventListener('click', () => this.open());
    this.querySelector('[data-close]').addEventListener('click', () => this.close());
    this.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.close();
      if (e.key === 'Tab') this.#trapFocus(e);
    });
  }
  open() {
    this.previouslyFocused = document.activeElement;   // remember trigger
    this.dialog.hidden = false;
    this.trigger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    this.#focusables()[0]?.focus();                    // move focus in
  }
  close() {
    this.dialog.hidden = true;
    this.trigger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    this.previouslyFocused?.focus();                   // return focus
  }
  #focusables() {
    return [...this.dialog.querySelectorAll(
      'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )];
  }
  #trapFocus(e) {
    const f = this.#focusables();
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }
}
customElements.define('cart-drawer', CartDrawer);
```
This is the reusable pattern for ALL modals/drawers: remember trigger → open → focus in → trap →
ESC/close → return focus.

---

## 13. Per-component a11y checklist

**Header / nav**
- [ ] `<nav aria-label>`, `aria-current="page"` on active item, `aria-expanded` on submenus,
      keyboard + ESC on dropdowns, logo link has accessible name.

**Drawers / modals (cart, menu, search, quick-add)**
- [ ] `role="dialog"`, `aria-modal`, labeled, focus moved in, focus trapped, ESC closes, focus
      returns to trigger, background scroll locked.

**Product form**
- [ ] Variant selectors labeled (`<fieldset>/<legend>`), quantity input labeled, add-to-cart is
      a `<button>`, success/error announced via live region, price changes announced.

**Media / gallery**
- [ ] Thumbnails are buttons with labels, alt text from image object, zoom keyboard-accessible,
      video not auto-playing with sound.

**Carousel / slideshow**
- [ ] `aria-roledescription`, slide labels "n of m", prev/next are labeled buttons, pause
      control, respects reduced motion, keyboard arrow support.

**Accordion / tabs**
- [ ] Native `<details>` or proper ARIA; Arrow-key nav for tabs; panels linked by id.

**Forms (contact, newsletter, login)**
- [ ] Every field labeled, errors with `aria-describedby`+`role="alert"`, correct `autocomplete`.

**Global**
- [ ] Skip link, single h1, logical heading order, all focus states visible (`:focus-visible`),
      contrast pairs pass in every scheme, reduced motion honored, no color-only meaning,
      `.visually-hidden` context on icon buttons & prices, live region for cart.
- [ ] Passes automated pass (axe / Lighthouse a11y ≥ 95) AND manual keyboard + SR spot check.
