# Contributing

Thanks for your interest in improving **shopify-theme-builder**! Contributions of
all sizes are welcome — new reference docs, extra example sections, scaffold
fixes, or docs polish.

## Ways to help

- **New sections** — add reference-quality sections to `examples/` or the
  scaffold, pattern-matched against [`examples/section-hero.liquid`](examples/section-hero.liquid).
- **References** — extend the guides in [`references/`](references/) (accessibility,
  performance, SEO, i18n/RTL, …).
- **Agent adapters** — improve support for another coding agent (add a rules file
  that points back to `AGENTS.md`).
- **Bug reports** — open an issue describing what the skill produced vs. what you
  expected.

## Ground rules (keep the quality bar)

Any theme code you add must honor the three hard constraints from `SKILL.md`:

1. **Shopify-compliant** — valid `{% schema %}`, `theme-check` clean, no
   deprecated Liquid; mirror Dawn when unsure.
2. **100% theme-editor controllable** — no hard-coded text/color/font/image/
   layout; everything is a setting, block, or section group.
3. **Systemized** — read `var(--token)` only; never literal colors/sizes.

## Before you open a PR

```bash
# structural check (JSON, schemas, references)
python scripts/validate_theme.py assets/theme-skeleton

# full Shopify validation (requires Shopify CLI)
shopify theme check assets/theme-skeleton
```

Keep PRs focused, describe the change, and update the relevant reference doc if
you introduce a new pattern. By contributing you agree your work is licensed
under the repository's [MIT license](LICENSE).
