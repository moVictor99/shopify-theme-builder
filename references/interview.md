# Phase 0 Discovery Interview

This is your **question bank** for the Phase 0 discovery interview — the conversation you run *before* architecting the theme. Its job is to extract exactly enough about the store's strategy, brand, market, scope, features, data model, and constraints to commit to a Phase 1 architecture with no rework.

## How to run it

- **Use the `AskUserQuestion` tool**, batching questions into the groups below (A–G). Present a group at a time; don't interrogate one question per message.
- **Be adaptive.** Skip anything already answered (from the initial brief, a brand brief, an existing store, or a prior group's answer). Never re-ask what you know.
- **Always offer "You decide."** For every design/feature choice, include a "You decide (recommended)" option so the user can delegate taste to you. When they pick it, apply the stated default and record the assumption.
- **State assumptions out loud.** Whenever you infer a default (because skipped or "you decide"), write it into the Phase 0 summary as an explicit assumption the user can veto later.
- **Bias to shipping.** If the user says "just build it," skip straight to the defaults table at the end and confirm only the archetype + languages.

Each group below gives: the **questions**, the **defaults to infer if skipped**, and notes.

---

## Group A — Orientation & strategy

**Questions**

1. **Store archetype?** (drives homepage sections + product template variant)
   - High-conversion DTC (few hero products, aggressive merchandising)
   - Editorial / content-led (story-first, lookbook, blog-heavy)
   - Catalog browse (large SKU count, filtering, collections-first)
   - Single-product landing (one hero product, long-form landing page)
   - Subscription (recurring product, plan selection)
   - Hybrid (name the mix)
2. **Primary homepage action?** What is the one thing a first-time visitor should do — shop a featured collection, add the hero product, read the story, subscribe, find a store?
3. **Who is the customer?** (demographic, price sensitivity, mobile-vs-desktop skew, new-vs-returning)
4. **Vertical & product type?** Category (fashion, beauty, food, electronics, home…) and nature: physical / digital / service / bundle.

**Defaults if skipped**

- Archetype: **High-conversion DTC** (the safest revenue-oriented default).
- Primary action: **Shop featured collection / add hero product.**
- Customer: **Mobile-first, mixed new/returning, mid-market price.**
- Product type: **Physical goods.**

---

## Group B — Brand & design direction

**Questions**

1. **Aesthetic?** minimal / bold / luxury / playful / editorial / techy (pick 1–2).
2. **1–2 reference brands or sites** you want to feel adjacent to (for tone calibration).
3. **Existing assets?** logo (formats), brand palette (hex values), brand fonts (licensed/Google/Adobe), photography style.
4. **Token preferences or "you decide"** for each of:
   - Color (primary/accent/neutrals, light or dark base)
   - Type (heading vs body families, scale feel — tight/airy)
   - Spacing (compact vs generous rhythm)
   - Radius (sharp / soft / pill)

**Defaults if skipped**

- Aesthetic: **Minimal** with one confident accent color.
- References: none — you set the tone.
- Assets: assume **logo provided**; if palette/fonts absent, you generate a token set (neutral base + single accent, one heading + one body family, system-safe + Arabic-capable fallback).
- Tokens: **You decide** — an 8-pt spacing scale, soft radius (`--radius-md` ~8px), restrained shadow scale, tasteful motion.

> Every design answer maps to the shared token vocabulary (`--color-*`, `--font-*`, `--space-*`, radius/shadow/motion scales). "You decide" = you pick token values; the merchant still adjusts them in the theme editor.

---

## Group C — Language & market

**Questions**

1. **Which languages** at launch? (and which is default/primary)
2. **RTL / Arabic bilingual?** Yes/No — if any RTL language, RTL is built in from day one.
3. **Currency & market(s)?** single market or Shopify Markets multi-currency/multi-region.
4. **Locale formatting** expectations — number/date format, currency placement.

**Defaults if skipped**

- Languages: **English default**, architecture **RTL-ready** (logical CSS everywhere) even if Arabic isn't enabled yet — so enabling `ar` later is a content task, not a rebuild.
- RTL: **Build RTL-capable regardless.** (Given this skill's mandate, always treat AR/EN + RTL as the default posture.)
- Market: **Single market**, currency from shop settings, `money`/`money_with_currency` filters (never hard-coded symbols).

---

## Group D — Scope (templates & pages)

**Questions**

Which of these ship in v1? (check all)

- Home, Product, Collection, Cart, Search
- Blog, Article
- Page (generic), About, Contact, FAQ
- 404, Password, Gift card
- Customer/account set (login, register, account, orders, addresses)
- **Custom landing / campaign templates** (named, e.g. `page.campaign-ramadan`)?

**Defaults if skipped**

- Ship the **full standard OS 2.0 set**: `index`, `product`, `collection`, `list-collections`, `cart`, `search`, `blog`, `article`, `page`, `page.contact`, `404`, `password`, `gift_card`, and the full `customers/*` set.
- Custom landing templates: **none** unless requested (add as JSON templates + section variants when a campaign need appears).

---

## Group E — Features & sections

Batch into sub-groups; ask what matters for the archetype, default the rest.

**E1 — Merchandising**

- Navigation: mega menu vs simple dropdown; predictive search on/off.
- PDP: gallery style (thumbnails / stacked / carousel / zoom), variant UI (swatches vs dropdown), quantity selector, bundles.
- Cart: cart drawer vs cart page; sticky add-to-cart on PDP; quick-add on cards.
- Recommendations: upsell/cross-sell, recently viewed, related products.
- Urgency: countdown timer, low-stock indicator.

**E2 — Trust / social proof**

- Reviews app (which — Judge.me, Loox, Yotpo, Okendo, Shopify Product Reviews) → surfaces via metafield + JSON-LD `aggregateRating`.
- UGC gallery, trust badges, testimonials section.

**E3 — Content**

- Rich text, image-with-text, editorial/lookbook, blog layout (grid/list/magazine).

**E4 — Marketing integrations / app blocks**

- Klaviyo / email capture, WhatsApp button, subscription app (Recharge/Seal), review app blocks, other pixels.

**Defaults if skipped (by archetype)**

| Feature | DTC | Editorial | Catalog | Single-product | Subscription |
| --- | --- | --- | --- | --- | --- |
| Nav | Simple dropdown | Simple | **Mega menu** | Minimal | Simple |
| Predictive search | On | On | **On** | Off | On |
| PDP gallery | Carousel + zoom | Stacked | Thumbnails | Stacked long-form | Carousel |
| Variant UI | **Swatches** | Swatches | Dropdown | Swatches | Plan selector |
| Cart | **Drawer** | Drawer | Page | Drawer | Drawer |
| Sticky ATC | **On** | Off | Off | **On** | On |
| Quick-add | On | Off | **On** | n/a | On |
| Upsell/cross-sell | **On** | Off | On | On | On |
| Recently viewed | On | Off | **On** | Off | Off |
| Urgency | Optional | Off | Off | **On** | Off |
| Reviews | **On** | On | On | **On** | On |
| Klaviyo/email | **On** | On | On | On | On |

- Marketing apps: build **app-block-ready** sections (Shopify app blocks) rather than hard integrations, unless a specific app is named.

---

## Group F — Data model (metafields)

**Questions**

1. **Product metafields** needed? (ingredients, size chart, care, badges, highlights, video, downloadable spec…) and **how each surfaces** (PDP tab, badge, callout).
2. **Collection metafields?** (hero image, editorial intro, banner copy).
3. **Page metafields?** (for custom landing content blocks).
4. Reviews metafield namespace (from the chosen app) for JSON-LD.

**Defaults if skipped**

- Define a **small conventional metafield set**: `product.custom.highlights` (list), `product.custom.size_chart` (page/richtext ref), `product.custom.badge` (single line), `product.reviews.rating` + `product.reviews.rating_count` (from review app). Surface highlights as PDP callouts, badge on card + PDP.
- Reference metafields with fallbacks (`{% if product.metafields... %}`) so sections render cleanly when unset — never assume presence.
- Everything metafield-driven remains **editor-visible** where possible; nothing hard-coded.

---

## Group G — Constraints

**Questions**

1. **Performance targets?** (Lighthouse/CWV goals, LCP budget, Theme Store perf requirements.)
2. **Accessibility level?** (WCAG 2.1 AA is the Theme Store baseline — confirm or higher.)
3. **Browser support?** (evergreen only, or specific legacy needs.)
4. **Deadline / phasing.**
5. **App dependencies** that must be accommodated (checkout extensions, subscription, reviews, loyalty, etc.).

**Defaults if skipped**

- Performance: **Theme Store perf bar** — Lighthouse ≥ 60 mobile floor, target LCP < 2.5s; lazy-load below-fold, responsive images, minimal JS.
- Accessibility: **WCAG 2.1 AA** (non-negotiable Theme Store requirement).
- Browsers: **evergreen** (last 2 versions Chrome/Safari/Firefox/Edge) + mobile Safari/Chrome.
- Deadline: none stated → sensible build order (foundation → templates → sections → polish).
- Apps: **app-block-ready**; no hard app coupling unless named.

---

## Translating answers into Phase 1 architecture

Use the archetype (Group A) as the master switch; it selects the homepage section stack and the product-template variant. Layer Group E answers on top.

**Archetype → homepage section stack**

| Archetype | Homepage sections (top → bottom) |
| --- | --- |
| High-conversion DTC | Hero (single CTA) → featured product/hero ATC → featured collection → benefits/icon row → reviews → email capture |
| Editorial | Full-bleed hero image → editorial story (image-with-text) → lookbook/gallery → featured collection → blog posts → newsletter |
| Catalog browse | Slim hero/announcement → collection list grid → featured collection(s) → predictive-search prominence → brand strip |
| Single-product landing | Hero with ATC → problem/solution → features (image-with-text ×N) → social proof → FAQ → sticky ATC + email |
| Subscription | Hero → how-it-works steps → plan/product selector → benefits → reviews → FAQ |
| Hybrid | Compose from the above per stated priority |

**Archetype → product template variant**

| Archetype | `product` template variant |
| --- | --- |
| DTC | Conversion PDP: gallery + swatches + sticky ATC + upsell + reviews block |
| Editorial | Story PDP: large media, richtext narrative, understated ATC |
| Catalog | Efficient PDP: thumbnail gallery, dropdown variants, spec tabs (metafields) |
| Single-product | Long-form landing PDP (may be `product.landing` JSON template) |
| Subscription | PDP with plan selector + subscription app block |

**Other mappings**

- **Group B aesthetic → token values** (`--color-*`, `--font-*`, radius/shadow/motion). Luxury → generous spacing, serif heading, sharp/small radius, subtle motion. Playful → bold accent, rounder radius, springier motion.
- **Group C RTL → build posture:** logical CSS properties + `dir` handling from the first stylesheet (see `references/i18n-rtl.md`), regardless of launch languages.
- **Group E reviews app → metafield + JSON-LD** `aggregateRating` (see `references/seo-structured-data.md`).
- **Group F metafields → section settings + PDP blocks** with presence guards.
- **Group G constraints → global perf/a11y budget** applied to every section.

---

## Defaults if the user says "just build it"

Confirm only **archetype** and **languages**; apply everything below and record as assumptions.

| Dimension | Default |
| --- | --- |
| Archetype | High-conversion DTC |
| Homepage stack | Hero → featured product → featured collection → benefits row → reviews → email capture |
| Product template | Conversion PDP (gallery + swatches + sticky ATC + upsell + reviews) |
| Aesthetic | Minimal, one accent color |
| Tokens | 8-pt spacing, soft radius (~8px), restrained shadows, tasteful motion; neutral base + single accent |
| Type | One heading + one body family, Arabic-capable fallback stack |
| Languages | English default, **RTL-ready** architecture |
| Market | Single market, `money` filters, currency from shop |
| Templates | Full standard OS 2.0 set (no custom landing) |
| Nav / search | Simple dropdown + predictive search on |
| Cart | Cart drawer + quick-add on cards |
| PDP extras | Sticky ATC, upsell, recently viewed, reviews block |
| Trust | Reviews app-block-ready + testimonials + trust badges section |
| Marketing | Email capture + app-block-ready sections (no hard app coupling) |
| Metafields | Conventional set: highlights, size_chart, badge, reviews rating/count |
| Performance | Theme Store perf bar; lazy-load, responsive images, minimal JS |
| Accessibility | WCAG 2.1 AA |
| Browsers | Evergreen + mobile Safari/Chrome |
| Content control | 100% theme-editor controllable; zero hard-coded shopper-facing strings |
