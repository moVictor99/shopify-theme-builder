# Design Tokens: The Single Source of Truth

This is the heart of the theme. Every color, size, radius, shadow, and motion value in the
entire theme derives from ONE token layer. A merchant changes a setting in the theme editor →
`settings_schema.json` value changes → `snippets/css-variables.liquid` re-emits CSS custom
properties → the whole theme restyles. Sections and snippets NEVER hard-code a color, size,
font, or duration. They only read `var(--token)`.

**The iron rule:** If you type a literal `#hex`, `px`, `rem`, `ms`, or font family name anywhere
in a section/snippet/base stylesheet, you have made a mistake. The only place literals live is
`css-variables.liquid` (deriving from settings) and the token scales below.

---

## 1. The token vocabulary (memorize these exact names)

### Color (per color-scheme group — RGB triplets so you can `rgb(var(--x) / <alpha>)`)
```
--color-background      --color-foreground     --color-surface     --color-border
--color-primary         --color-on-primary     --color-secondary   --color-accent
--color-sale            --color-focus
```
Emit each as a **space-separated RGB triplet** (`24 24 27`), NOT `rgb(...)`. This lets any
consumer add alpha: `background: rgb(var(--color-surface) / 0.6);`.

### Typography
```
--font-heading-family   --font-body-family     --font-heading-weight  --font-body-weight
--font-h1 --font-h2 --font-h3 --font-h4 --font-h5 --font-h6           (fluid clamp scale)
--font-body             --font-small
--line-heading          --line-body
```

### Space
```
--page-width            --section-padding-block  --grid-gap
--space-1 … --space-12  (8pt scale)
```

### Radius / Shadow / Motion
```
--radius-sm --radius-md --radius-lg --radius-pill
--shadow-sm --shadow-md --shadow-lg
--ease  --duration-fast --duration-base --duration-slow
```

---

## 2. `settings_schema.json` — the token groups

The theme editor UI is generated from `config/settings_schema.json`. Each group below produces
settings that `css-variables.liquid` reads. Every setting has `label`, and groups have `header`
and `info` where helpful. All labels/info reference translation keys in `locales/*.schema.json`.

### 2a. Colors — via `color_scheme_group`

Colors are NOT global settings. Dawn-style themes use a **color scheme group**: the merchant
defines N schemes (e.g. "Scheme 1", "Scheme 2", "Inverse", "Accent") each with a full palette,
then every section picks a scheme. This is what makes a theme feel cohesive and fully editable.

```json
{
  "name": "t:settings_schema.colors.name",
  "settings": [
    {
      "type": "color_scheme_group",
      "id": "color_schemes",
      "definition": [
        {
          "type": "color",
          "id": "background",
          "label": "t:settings_schema.colors.settings.background.label",
          "default": "#FFFFFF"
        },
        {
          "type": "color",
          "id": "foreground",
          "label": "t:settings_schema.colors.settings.foreground.label",
          "default": "#121212"
        },
        {
          "type": "color",
          "id": "surface",
          "label": "t:settings_schema.colors.settings.surface.label",
          "default": "#F5F5F5"
        },
        {
          "type": "color",
          "id": "border",
          "label": "t:settings_schema.colors.settings.border.label",
          "default": "#E1E1E1"
        },
        {
          "type": "color",
          "id": "primary",
          "label": "t:settings_schema.colors.settings.primary.label",
          "default": "#121212"
        },
        {
          "type": "color",
          "id": "on_primary",
          "label": "t:settings_schema.colors.settings.on_primary.label",
          "default": "#FFFFFF"
        },
        {
          "type": "color",
          "id": "secondary",
          "label": "t:settings_schema.colors.settings.secondary.label",
          "default": "#334FB4"
        },
        {
          "type": "color",
          "id": "accent",
          "label": "t:settings_schema.colors.settings.accent.label",
          "default": "#C99C5A"
        },
        {
          "type": "color",
          "id": "sale",
          "label": "t:settings_schema.colors.settings.sale.label",
          "default": "#D02E2E"
        },
        {
          "type": "color",
          "id": "focus",
          "label": "t:settings_schema.colors.settings.focus.label",
          "default": "#005FCC"
        }
      ],
      "role": {
        "background": "background",
        "text": "foreground",
        "primary_button": "primary",
        "on_primary_button": "on_primary",
        "primary_button_border": "primary",
        "secondary_button_label": "secondary",
        "links": "secondary"
      }
    }
  ]
}
```

> The `role` object tells the theme editor which token drives which native UI concept (button
> previews, etc.). Keep it aligned with your CSS usage.

### 2b. Typography — via `font_picker` (+ derived weights/scale)

```json
{
  "name": "t:settings_schema.typography.name",
  "settings": [
    {
      "type": "header",
      "content": "t:settings_schema.typography.settings.headings_header.content"
    },
    {
      "type": "font_picker",
      "id": "heading_font",
      "label": "t:settings_schema.typography.settings.heading_font.label",
      "default": "assistant_n4"
    },
    {
      "type": "range",
      "id": "heading_scale",
      "min": 100, "max": 150, "step": 5, "unit": "%",
      "label": "t:settings_schema.typography.settings.heading_scale.label",
      "info": "t:settings_schema.typography.settings.heading_scale.info",
      "default": 120
    },
    {
      "type": "header",
      "content": "t:settings_schema.typography.settings.body_header.content"
    },
    {
      "type": "font_picker",
      "id": "body_font",
      "label": "t:settings_schema.typography.settings.body_font.label",
      "default": "assistant_n4"
    },
    {
      "type": "range",
      "id": "body_scale",
      "min": 90, "max": 130, "step": 5, "unit": "%",
      "label": "t:settings_schema.typography.settings.body_scale.label",
      "default": 100
    }
  ]
}
```

- `font_picker` returns a **font object**. In Liquid you get `settings.heading_font.family`,
  `.fallback_families`, `.weight`, `.style`, and you pass the object to `font_face` and `font_modify`.
- **Weights:** derive a bold heading with `font_modify: 'weight', 'bolder'` and never hard-code
  `font-weight: 700`. Expose the base weight as `--font-heading-weight`.
- **Scale:** `heading_scale` / `body_scale` are multipliers folded into the `clamp()` type scale.

### 2c. Layout — page width / section padding / grid gap

```json
{
  "name": "t:settings_schema.layout.name",
  "settings": [
    {
      "type": "range",
      "id": "page_width",
      "min": 1000, "max": 1600, "step": 20, "unit": "px",
      "label": "t:settings_schema.layout.settings.page_width.label",
      "default": 1200
    },
    {
      "type": "range",
      "id": "section_padding_block",
      "min": 0, "max": 100, "step": 4, "unit": "px",
      "label": "t:settings_schema.layout.settings.section_padding_block.label",
      "info": "t:settings_schema.layout.settings.section_padding_block.info",
      "default": 48
    },
    {
      "type": "range",
      "id": "grid_gap",
      "min": 8, "max": 48, "step": 2, "unit": "px",
      "label": "t:settings_schema.layout.settings.grid_gap.label",
      "default": 16
    }
  ]
}
```

### 2d. Corners — radius ranges

```json
{
  "name": "t:settings_schema.corners.name",
  "settings": [
    { "type": "range", "id": "radius_sm", "min": 0, "max": 12, "step": 1, "unit": "px",
      "label": "t:settings_schema.corners.settings.radius_sm.label", "default": 4 },
    { "type": "range", "id": "radius_md", "min": 0, "max": 24, "step": 1, "unit": "px",
      "label": "t:settings_schema.corners.settings.radius_md.label", "default": 8 },
    { "type": "range", "id": "radius_lg", "min": 0, "max": 40, "step": 1, "unit": "px",
      "label": "t:settings_schema.corners.settings.radius_lg.label", "default": 16 }
  ]
}
```
`--radius-pill` is a constant (`9999px`) — not merchant-editable.

### 2e. Shadows

```json
{
  "name": "t:settings_schema.shadows.name",
  "settings": [
    { "type": "range", "id": "shadow_opacity", "min": 0, "max": 40, "step": 5, "unit": "%",
      "label": "t:settings_schema.shadows.settings.shadow_opacity.label", "default": 10 },
    { "type": "range", "id": "shadow_blur", "min": 0, "max": 40, "step": 2, "unit": "px",
      "label": "t:settings_schema.shadows.settings.shadow_blur.label", "default": 16 }
  ]
}
```
Compose the three shadow tokens from `shadow_opacity` + `shadow_blur` (see the bridge).

### 2f. Buttons

```json
{
  "name": "t:settings_schema.buttons.name",
  "settings": [
    { "type": "range", "id": "button_radius", "min": 0, "max": 40, "step": 2, "unit": "px",
      "label": "t:settings_schema.buttons.settings.button_radius.label", "default": 8 },
    { "type": "range", "id": "button_border_width", "min": 0, "max": 4, "step": 1, "unit": "px",
      "label": "t:settings_schema.buttons.settings.button_border_width.label", "default": 1 }
  ]
}
```

### 2g. Animation / motion toggle

```json
{
  "name": "t:settings_schema.animation.name",
  "settings": [
    { "type": "checkbox", "id": "animations_enabled",
      "label": "t:settings_schema.animation.settings.animations_enabled.label",
      "default": true },
    { "type": "select", "id": "animation_speed",
      "label": "t:settings_schema.animation.settings.animation_speed.label",
      "options": [
        { "value": "fast",   "label": "t:settings_schema.animation.settings.animation_speed.options__1.label" },
        { "value": "normal", "label": "t:settings_schema.animation.settings.animation_speed.options__2.label" },
        { "value": "slow",   "label": "t:settings_schema.animation.settings.animation_speed.options__3.label" }
      ],
      "default": "normal" }
  ]
}
```

---

## 3. The bridge: `snippets/css-variables.liquid`

Rendered once, high in `layout/theme.liquid`'s `<head>`, right after the `<meta>` tags and
before any stylesheet. It emits `:root` globals and one `.color-<scheme-id>` block per scheme.

```liquid
{%- comment -%}
  snippets/css-variables.liquid
  THE ONLY place literals are converted into design tokens.
  Rendered in <head> before stylesheets. No section reads settings.* for style — only var(--token).
{%- endcomment -%}

{%- liquid
  # motion
  assign motion_enabled = settings.animations_enabled
  case settings.animation_speed
    when 'fast'   then assign dur_base = 150
    when 'slow'   then assign dur_base = 450
    else               assign dur_base = 300
  endcase
  assign dur_fast = dur_base | times: 0.5 | round
  assign dur_slow = dur_base | times: 1.5 | round
-%}

{%- comment -%} @font-face declarations for the picked fonts + bold variants {%- endcomment -%}
{%- assign heading_bold = settings.heading_font | font_modify: 'weight', 'bolder' -%}
{%- assign body_bold    = settings.body_font    | font_modify: 'weight', 'bolder' -%}
{{ settings.heading_font | font_face: font_display: 'swap' }}
{{ heading_bold          | font_face: font_display: 'swap' }}
{{ settings.body_font    | font_face: font_display: 'swap' }}
{{ body_bold             | font_face: font_display: 'swap' }}

{% style %}
  :root {
    /* ---- Typography ---- */
    --font-heading-family: {{ settings.heading_font.family }}, {{ settings.heading_font.fallback_families }};
    --font-body-family: {{ settings.body_font.family }}, {{ settings.body_font.fallback_families }};
    --font-heading-weight: {{ settings.heading_font.weight }};
    --font-body-weight: {{ settings.body_font.weight }};
    --line-heading: 1.15;
    --line-body: 1.6;

    /* Fluid modular scale — heading_scale/body_scale fold into the max side of clamp() */
    {%- assign hs = settings.heading_scale | divided_by: 100.0 -%}
    {%- assign bs = settings.body_scale | divided_by: 100.0 -%}
    --font-h1: clamp({{ 1.802 | times: bs | round: 3 }}rem, {{ 1.2 | times: bs }}rem + 2.6vw, {{ 3.815 | times: hs | round: 3 }}rem);
    --font-h2: clamp({{ 1.602 | times: bs | round: 3 }}rem, {{ 1.1 | times: bs }}rem + 1.9vw, {{ 3.052 | times: hs | round: 3 }}rem);
    --font-h3: clamp({{ 1.424 | times: bs | round: 3 }}rem, {{ 1.0 | times: bs }}rem + 1.3vw, {{ 2.441 | times: hs | round: 3 }}rem);
    --font-h4: clamp({{ 1.266 | times: bs | round: 3 }}rem, {{ 0.95 | times: bs }}rem + 0.8vw, {{ 1.953 | times: hs | round: 3 }}rem);
    --font-h5: clamp({{ 1.125 | times: bs | round: 3 }}rem, {{ 0.9 | times: bs }}rem + 0.4vw, {{ 1.563 | times: hs | round: 3 }}rem);
    --font-h6: clamp({{ 1.0 | times: bs | round: 3 }}rem, {{ 0.9 | times: bs }}rem + 0.2vw, {{ 1.25 | times: hs | round: 3 }}rem);
    --font-body: clamp({{ 0.95 | times: bs | round: 3 }}rem, {{ 0.9 | times: bs }}rem + 0.2vw, {{ 1.0 | times: bs | round: 3 }}rem);
    --font-small: {{ 0.833 | times: bs | round: 3 }}rem;

    /* ---- Space (8pt) ---- */
    --page-width: {{ settings.page_width }}px;
    --section-padding-block: {{ settings.section_padding_block }}px;
    --grid-gap: {{ settings.grid_gap }}px;
    --space-1: 4px;  --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
    --space-5: 24px; --space-6: 32px;  --space-7: 40px;  --space-8: 48px;
    --space-9: 64px; --space-10: 80px; --space-11: 96px; --space-12: 128px;

    /* ---- Corners ---- */
    --radius-sm: {{ settings.radius_sm }}px;
    --radius-md: {{ settings.radius_md }}px;
    --radius-lg: {{ settings.radius_lg }}px;
    --radius-pill: 9999px;
    --button-radius: {{ settings.button_radius }}px;
    --button-border-width: {{ settings.button_border_width }}px;

    /* ---- Shadows (composed from opacity + blur) ---- */
    {%- assign so = settings.shadow_opacity | divided_by: 100.0 -%}
    --shadow-sm: 0 1px {{ settings.shadow_blur | divided_by: 3 }}px rgb(18 18 18 / {{ so | times: 0.6 | round: 2 }});
    --shadow-md: 0 4px {{ settings.shadow_blur }}px rgb(18 18 18 / {{ so | round: 2 }});
    --shadow-lg: 0 12px {{ settings.shadow_blur | times: 2 }}px rgb(18 18 18 / {{ so | times: 1.4 | round: 2 }});

    /* ---- Motion ---- */
    --ease: cubic-bezier(0.4, 0, 0.2, 1);
    --duration-fast: {% if motion_enabled %}{{ dur_fast }}ms{% else %}0ms{% endif %};
    --duration-base: {% if motion_enabled %}{{ dur_base }}ms{% else %}0ms{% endif %};
    --duration-slow: {% if motion_enabled %}{{ dur_slow }}ms{% else %}0ms{% endif %};
  }

  /* ---- Per-color-scheme blocks ---- */
  {%- for scheme in settings.color_schemes -%}
    {%- assign s = scheme.settings -%}
    .color-{{ scheme.id }} {
      --color-background: {{ s.background.red }} {{ s.background.green }} {{ s.background.blue }};
      --color-foreground: {{ s.foreground.red }} {{ s.foreground.green }} {{ s.foreground.blue }};
      --color-surface: {{ s.surface.red }} {{ s.surface.green }} {{ s.surface.blue }};
      --color-border: {{ s.border.red }} {{ s.border.green }} {{ s.border.blue }};
      --color-primary: {{ s.primary.red }} {{ s.primary.green }} {{ s.primary.blue }};
      --color-on-primary: {{ s.on_primary.red }} {{ s.on_primary.green }} {{ s.on_primary.blue }};
      --color-secondary: {{ s.secondary.red }} {{ s.secondary.green }} {{ s.secondary.blue }};
      --color-accent: {{ s.accent.red }} {{ s.accent.green }} {{ s.accent.blue }};
      --color-sale: {{ s.sale.red }} {{ s.sale.green }} {{ s.sale.blue }};
      --color-focus: {{ s.focus.red }} {{ s.focus.green }} {{ s.focus.blue }};

      color: rgb(var(--color-foreground));
      background-color: rgb(var(--color-background));
    }
  {%- endfor -%}

  @media (prefers-reduced-motion: reduce) {
    :root {
      --duration-fast: 0ms;
      --duration-base: 0ms;
      --duration-slow: 0ms;
    }
  }
{% endstyle %}
```

> `scheme.settings.<color>.red/.green/.blue` come from the Liquid `color` object — that is how
> you get the RGB triplet. Never `| color_to_rgb` string-parse; use the numeric channels.

### Base stylesheet consumes tokens only
In `assets/base.css` (or a `{% stylesheet %}`), you reference tokens exclusively:
```css
body { font-family: var(--font-body-family); font-weight: var(--font-body-weight);
       font-size: var(--font-body); line-height: var(--line-body); }
h1 { font-family: var(--font-heading-family); font-weight: var(--font-heading-weight);
     font-size: var(--font-h1); line-height: var(--line-heading); }
.page-width { max-width: var(--page-width); margin-inline: auto; padding-inline: var(--space-4); }
.card { background: rgb(var(--color-surface)); border: 1px solid rgb(var(--color-border));
        border-radius: var(--radius-md); box-shadow: var(--shadow-sm); }
.button {
  background: rgb(var(--color-primary)); color: rgb(var(--color-on-primary));
  border: var(--button-border-width) solid rgb(var(--color-primary));
  border-radius: var(--button-radius);
  transition: transform var(--duration-fast) var(--ease), background var(--duration-fast) var(--ease);
}
.price--on-sale { color: rgb(var(--color-sale)); }
```

---

## 4. How a section applies a scheme

Every section that renders visible surface exposes a `color_scheme` setting and applies the
class. Section padding uses the token too.

**Section schema:**
```json
{
  "settings": [
    {
      "type": "color_scheme",
      "id": "color_scheme",
      "label": "t:sections.all.color_scheme.label",
      "default": "scheme-1"
    }
  ]
}
```

**Section markup:**
```liquid
<div class="color-{{ section.settings.color_scheme }} section">
  <div class="page-width">
    {{ section.settings.heading }}
  </div>
</div>

{% stylesheet %}
  .section { padding-block: var(--section-padding-block); }
{% endstylesheet %}
```

Because `.color-<scheme>` sets `--color-*` and `color`/`background-color`, every descendant that
reads `rgb(var(--color-foreground))` etc. automatically adapts. Nesting a different
`.color-<scheme>` inside re-scopes it. This is the whole trick.

---

## 5. The scales (reference tables)

### 8pt spacing scale
| Token | Value | Typical use |
|-------|-------|-------------|
| `--space-1` | 4px | icon gaps, hairline insets |
| `--space-2` | 8px | tight padding, chip gaps |
| `--space-3` | 12px | input padding |
| `--space-4` | 16px | default gap, card padding |
| `--space-5` | 24px | between blocks |
| `--space-6` | 32px | card padding (spacious) |
| `--space-7` | 40px | small section rhythm |
| `--space-8` | 48px | section padding (default) |
| `--space-9` | 64px | large section rhythm |
| `--space-10` | 80px | hero padding |
| `--space-11` | 96px | major section gaps |
| `--space-12` | 128px | oversized hero/spacer |

### Modular type scale (ratio 1.25 "major third", fluid via clamp)
The min is roughly a 1.15 mobile ratio; the max is the 1.25 desktop ratio × `heading_scale`.
| Token | Step | min (rem) | max (rem, ×scale) | clamp middle |
|-------|------|-----------|-------------------|--------------|
| `--font-h1` | +5 | 1.802 | 3.815 | `1.2rem + 2.6vw` |
| `--font-h2` | +4 | 1.602 | 3.052 | `1.1rem + 1.9vw` |
| `--font-h3` | +3 | 1.424 | 2.441 | `1.0rem + 1.3vw` |
| `--font-h4` | +2 | 1.266 | 1.953 | `0.95rem + 0.8vw` |
| `--font-h5` | +1 | 1.125 | 1.563 | `0.9rem + 0.4vw` |
| `--font-h6` | 0 | 1.000 | 1.250 | `0.9rem + 0.2vw` |
| `--font-body` | base | 0.95 | 1.000 | `0.9rem + 0.2vw` |
| `--font-small` | −1 | 0.833 | 0.833 | fixed |

Fluid formula pattern: `clamp(<min>rem, <fluid-mid>, <max>rem)`. The middle term
(`<base>rem + <n>vw`) is what interpolates between viewport widths. Never use a bare `vw` sizing
without clamp bounds — it breaks accessibility zoom.

### Radius scale
| Token | Default | Range | Use |
|-------|---------|-------|-----|
| `--radius-sm` | 4px | 0–12 | inputs, badges |
| `--radius-md` | 8px | 0–24 | cards, buttons |
| `--radius-lg` | 16px | 0–40 | modals, media |
| `--radius-pill` | 9999px | fixed | pills, avatars |

### Shadow scale
| Token | Composition |
|-------|-------------|
| `--shadow-sm` | `0 1px (blur/3) rgb(18 18 18 / opacity·0.6)` |
| `--shadow-md` | `0 4px (blur) rgb(18 18 18 / opacity)` |
| `--shadow-lg` | `0 12px (blur·2) rgb(18 18 18 / opacity·1.4)` |

### Motion scale
| Token | fast | normal | slow | Notes |
|-------|------|--------|------|-------|
| `--duration-fast` | 75ms | 150ms | 225ms | hovers, taps |
| `--duration-base` | 150ms | 300ms | 450ms | drawers, fades |
| `--duration-slow` | 225ms | 450ms | 675ms | large reveals |
| `--ease` | `cubic-bezier(0.4, 0, 0.2, 1)` | | | standard easing |

All durations collapse to `0ms` when `animations_enabled` is off OR `prefers-reduced-motion`.

---

## 6. Token audit checklist

Run this before every commit. `theme-check` won't catch literals — you must.

- [ ] `grep -rniE '#[0-9a-f]{3,8}' sections snippets` returns **nothing** (no hex outside css-variables.liquid).
- [ ] `grep -rnE '[0-9]+px' sections snippets` returns nothing except inside `{% stylesheet %}`
      where it references a token, and even there prefer `var(--space-*)`.
- [ ] No `font-family:` naming a literal family outside `css-variables.liquid`.
- [ ] No `font-weight: 700` / literal weights — use `var(--font-heading-weight)` or `font_modify`.
- [ ] Every visible section has a `color_scheme` setting and `class="color-{{ ... }}"`.
- [ ] All colors emitted as RGB triplets; consumers use `rgb(var(--color-*) [/ alpha])`.
- [ ] Type sizes come from `--font-*` (clamp), never raw `rem`/`vw`.
- [ ] Spacing comes from `--space-*` / `--section-padding-block` / `--grid-gap`.
- [ ] Radii from `--radius-*` / `--button-radius`; shadows from `--shadow-*`.
- [ ] All transitions/animations use `--duration-*` + `--ease`; reduced-motion guarded.
- [ ] Changing ONE setting (e.g. `page_width`, a scheme color, `heading_scale`) visibly
      restyles the whole storefront — verify in the editor.
- [ ] `css-variables.liquid` is the ONLY file converting settings → literals.
- [ ] Every setting has `label`; groups have `header`/`info`; all strings are `t:` keys.
