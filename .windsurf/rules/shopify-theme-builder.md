---
trigger: model_decision
description: Build production-grade Online Store 2.0 Shopify themes — interview-first, 100% theme-editor controllable, token-driven, theme-check clean, bilingual/RTL. Use when building, generating, scaffolding, or designing a Shopify theme, sections, JSON templates, or Liquid.
---

# Shopify Theme Builder (Windsurf rule)

For any Shopify theme build/design task, follow this repo's workflow — it is
agent-agnostic and self-contained.

Start with `AGENTS.md` (or `SKILL.md`): full workflow, phase gates, and the
design-token vocabulary. Load `references/*.md` only when a phase needs them.
Copy `assets/theme-skeleton/` as the scaffold and pattern-match new sections
against `examples/section-hero.liquid`.

Never trade away the three hard constraints:
1. Shopify-compliant — valid `{% schema %}`, `theme-check` clean, no deprecated
   Liquid, mirror Dawn when unsure.
2. 100% theme-editor controllable — no hard-coded text/color/font/image/layout;
   everything is a setting, block, or section group.
3. Systemized — one token layer; sections use `var(--token)` only.

Gated phases: 0 interview (blocking) → 1 plan (approval) → 2 scaffold → 3 build
→ 4 design → 5 i18n/RTL → 6 QA (`shopify theme check` + `scripts/validate_theme.py`)
→ 7 package. Don't skip the interview; don't cross a gate early.
