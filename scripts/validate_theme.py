#!/usr/bin/env python3
"""
validate_theme.py — structural + import/sync landmine linter for an OS 2.0 theme.

This is NOT a replacement for `shopify theme check` (run that too). It catches two
classes of problems:

  STRUCTURAL (also caught, partly, by theme-check):
    * malformed JSON in templates, section groups, config, and locales
    * malformed JSON inside a section's {% schema %} block
    * missing required directories / files / templates
    * JSON templates that reference a section `type` with no matching section file
    * sections missing a {% schema %} entirely

  IMPORT / SYNC LANDMINES (theme-check does NOT catch these — they are the #1
  cause of "it validated but the store is broken"; see
  references/reliability-and-sync.md):
    * {% stylesheet %} / {% javascript %} tags  -> importer can silently drop the
      whole section (-> missing sections / 404s)                        [§1]
    * section block `name` > 25 chars            -> section + template dropped
      (-> 404)                                                          [§2]
    * invalid color_scheme_group `role` key      -> whole color system rejected
      (-> serif fallback)                                               [§3]
    * static {% section 'x' %} in a layout file  -> layout render aborts [§4]
    * a filter piped inside an image_tag arg     -> LiquidHTMLSyntaxError [§5]
    * cruft in the theme root / nested asset dirs -> import rejection / bloat [§14]

Usage:
    python scripts/validate_theme.py [THEME_DIR]

THEME_DIR defaults to the current directory. Exit code 0 = clean, 1 = errors.
Handles Shopify-style `//` and `/* */` comments in JSON template/config files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_DIRS = ["assets", "config", "layout", "sections", "snippets", "templates", "locales"]
REQUIRED_FILES = [
    "config/settings_schema.json",
    "config/settings_data.json",
    "layout/theme.liquid",
    "locales/en.default.json",
]
# Template name (any extension) -> at least one of these must exist as .json or .liquid
REQUIRED_TEMPLATES = [
    "index", "product", "collection", "list-collections", "page",
    "blog", "article", "cart", "search", "404", "password", "gift_card",
]

# Documented color_scheme_group role keys. ANYTHING else invalidates the whole
# group in the editor (theme-check does not check this). See reliability #3.
VALID_ROLE_KEYS = {
    "background", "text", "primary_button", "on_primary_button",
    "primary_button_border", "secondary_button", "on_secondary_button",
    "secondary_button_border", "links", "icons",
}

MAX_BLOCK_NAME_LEN = 25  # Shopify sync limit (reliability #2)

# Files/dirs that must never ship inside a theme (reliability #14).
CRUFT_NAMES = {
    "npm-cache", "node_modules", ".npm", ".shopify", ".git", "__pycache__",
    ".DS_Store", "Thumbs.db",
}
CRUFT_SUFFIXES = {".log", ".zip", ".pyc"}
# Dirs whose immediate contents must be flat (no subfolders), with exceptions.
FLAT_DIRS = {"assets", "snippets", "sections"}
FLAT_DIR_EXCEPTIONS = {"templates/customers", "templates/metaobject"}

SCHEMA_RE = re.compile(r"{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}", re.DOTALL)
LIQUID_COMMENT_RE = re.compile(r"{%-?\s*comment\s*-?%}.*?{%-?\s*endcomment\s*-?%}", re.DOTALL)
STYLESHEET_TAG_RE = re.compile(r"{%-?\s*(stylesheet|javascript)\s*-?%}")
STATIC_SECTION_RE = re.compile(r"{%-?\s*section\s+['\"]")
# From `image_tag:` up to the closing `}}` / `%}` of that output/tag.
IMAGE_TAG_ARGS_RE = re.compile(r"image_tag\s*:(.*?)(?:%}|}})", re.DOTALL)
CUSTOM_ELEMENT_RE = re.compile(r"customElements\.define\(\s*['\"]([a-z][a-z0-9-]*-[a-z0-9-]+)['\"]")

errors: list[str] = []
warnings: list[str] = []

# ---------------------------------------------------------------------------
# JSON helpers (Shopify tolerates // and /* */ comments in template/config JSON)
# ---------------------------------------------------------------------------


def strip_json_comments(text: str) -> str:
    out = []
    i, n = 0, len(text)
    in_str = False
    escape = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] not in "\r\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def load_json(path: Path, tolerant: bool = False):
    raw = path.read_text(encoding="utf-8")
    if tolerant:
        raw = strip_json_comments(raw)
    return json.loads(raw)


def blank_liquid_comments(text: str) -> str:
    """Replace {% comment %}..{% endcomment %} bodies with blanks, preserving
    newlines so reported line numbers stay accurate. Prevents false positives
    when a comment documents a forbidden construct (e.g. explains why NOT to use
    the {% stylesheet %} tag)."""
    def repl(m: "re.Match[str]") -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    return LIQUID_COMMENT_RE.sub(repl, text)


def load_schema_locale(theme: Path) -> dict:
    path = theme / "locales" / "en.default.schema.json"
    if not path.is_file():
        return {}
    try:
        return load_json(path)
    except (json.JSONDecodeError, OSError):
        return {}


def resolve_t(value, locale: dict):
    """Resolve a `t:a.b.c` key against the schema locale; return the string, or
    None if it can't be resolved. Non-`t:` values are returned unchanged."""
    if not isinstance(value, str):
        return value
    if not value.startswith("t:"):
        return value
    node = locale
    for part in value[2:].split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node if isinstance(node, str) else None


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------


def check_structure(theme: Path) -> None:
    for d in REQUIRED_DIRS:
        if not (theme / d).is_dir():
            errors.append(f"Missing required directory: {d}/")
    for f in REQUIRED_FILES:
        if not (theme / f).is_file():
            errors.append(f"Missing required file: {f}")
    for t in REQUIRED_TEMPLATES:
        json_t = theme / "templates" / f"{t}.json"
        liquid_t = theme / "templates" / f"{t}.liquid"
        if not json_t.is_file() and not liquid_t.is_file():
            errors.append(f"Missing required template: templates/{t}.json (or .liquid)")


def check_json_files(theme: Path) -> None:
    for sub in ["templates", "config", "locales", "sections"]:
        base = theme / sub
        if not base.is_dir():
            continue
        for path in base.rglob("*.json"):
            try:
                load_json(path, tolerant=(sub in {"templates", "config"}))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON: {path.relative_to(theme)} -> {exc}")


def check_section_schemas(theme: Path, locale: dict) -> dict[str, Path]:
    """Validate {% schema %} JSON, lint block names, and return available types."""
    available: dict[str, Path] = {}
    sections = theme / "sections"
    if not sections.is_dir():
        return available
    for path in sections.glob("*.liquid"):
        available[path.stem] = path
        text = path.read_text(encoding="utf-8")
        m = SCHEMA_RE.search(text)
        if not m:
            errors.append(f"Section without {{% schema %}}: sections/{path.name}")
            continue
        try:
            schema = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid schema JSON in sections/{path.name} -> {exc}")
            continue
        check_block_names(path, schema, locale)
    for path in sections.glob("*.json"):
        available[path.stem] = path
    return available


def check_block_names(path: Path, schema: dict, locale: dict) -> None:
    """Reliability §2: any block `name` > 25 chars is dropped on sync."""
    rel = path.relative_to(path.parents[1])  # sections/<file>
    for block in schema.get("blocks", []) or []:
        if not isinstance(block, dict):
            continue
        name = block.get("name")
        if name is None:
            continue
        resolved = resolve_t(name, locale)
        if resolved is None:
            warnings.append(
                f"{rel}: block name {name!r} is a t: key not found in "
                f"en.default.schema.json — cannot verify its length (must be <= "
                f"{MAX_BLOCK_NAME_LEN} chars rendered)."
            )
            continue
        if len(resolved) > MAX_BLOCK_NAME_LEN:
            errors.append(
                f"{rel}: block name {resolved!r} is {len(resolved)} chars "
                f"(> {MAX_BLOCK_NAME_LEN}). Shopify sync silently DROPS the section "
                f"+ its template (-> 404). Shorten it. [reliability #2]"
            )


def check_template_references(theme: Path, available: dict[str, Path]) -> None:
    templates = theme / "templates"
    if not templates.is_dir():
        return
    for path in templates.rglob("*.json"):
        try:
            data = load_json(path, tolerant=True)
        except json.JSONDecodeError:
            continue  # already reported
        for name, sec in (data.get("sections") or {}).items():
            stype = sec.get("type") if isinstance(sec, dict) else None
            if not stype or stype.startswith("@"):
                continue
            if stype not in available:
                errors.append(
                    f"{path.relative_to(theme)} references section '{stype}' "
                    f"but sections/{stype}.liquid does not exist"
                )


def check_settings_schema(theme: Path) -> None:
    """theme_info presence + color_scheme_group role validity (reliability #3)."""
    path = theme / "config" / "settings_schema.json"
    if not path.is_file():
        return
    try:
        data = load_json(path, tolerant=True)
    except json.JSONDecodeError:
        return
    if not isinstance(data, list) or not data:
        errors.append("config/settings_schema.json must be a non-empty array")
        return
    if not any(isinstance(g, dict) and g.get("name") == "theme_info" for g in data):
        warnings.append("config/settings_schema.json is missing a theme_info block")

    for group in data:
        if not isinstance(group, dict):
            continue
        for setting in group.get("settings", []) or []:
            if not isinstance(setting, dict):
                continue
            if setting.get("type") != "color_scheme_group":
                continue
            role = setting.get("role")
            if not isinstance(role, dict):
                continue
            bad = set(role.keys()) - VALID_ROLE_KEYS
            if bad:
                errors.append(
                    "config/settings_schema.json: color_scheme_group role has "
                    f"invalid key(s) {sorted(bad)}. A single unknown role key "
                    "invalidates the ENTIRE color system (editor: 'color schemes "
                    "must be defined', serif fallback). Valid keys: "
                    f"{sorted(VALID_ROLE_KEYS)}. [reliability #3]"
                )


# ---------------------------------------------------------------------------
# Import / sync landmine checks
# ---------------------------------------------------------------------------


def check_stylesheet_tags(theme: Path) -> None:
    """Reliability §1: {% stylesheet %} / {% javascript %} tags get dropped."""
    for sub in ["sections", "snippets"]:
        base = theme / sub
        if not base.is_dir():
            continue
        for path in base.rglob("*.liquid"):
            text = blank_liquid_comments(path.read_text(encoding="utf-8"))
            for m in STYLESHEET_TAG_RE.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                tag = m.group(1)
                errors.append(
                    f"{path.relative_to(theme)}:{line}: uses the {{% {tag} %}} tag. "
                    f"Shopify's importer can silently DROP this whole section/snippet "
                    f"(-> missing sections / 404s). Use a {{% style %}} tag for CSS, "
                    f"or an external assets/*.{('js' if tag=='javascript' else 'css')} "
                    f"file. [reliability #1]"
                )


def check_layout_static_sections(theme: Path) -> None:
    """Reliability §4: no static singular {% section 'x' %} in layout files."""
    layout = theme / "layout"
    if not layout.is_dir():
        return
    for path in layout.glob("*.liquid"):
        text = blank_liquid_comments(path.read_text(encoding="utf-8"))
        for m in STATIC_SECTION_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            errors.append(
                f"{path.relative_to(theme)}:{line}: static {{% section '...' %}} in a "
                f"layout. Mixing a static section with section groups ({{% sections "
                f"'...' %}}) aborts the layout render. Deliver header/footer/cart via "
                f"section groups instead. [reliability #4]"
            )


def check_image_tag_filters(theme: Path) -> None:
    """Reliability §5: a filter piped inside an image_tag argument.

    WARNING (not error) — the heuristic scans from `image_tag:` to the closing
    braces and flags a `|` inside; a filter there applies to the whole tag (or,
    for `| escape`, raises LiquidHTMLSyntaxError). Pre-compute the value instead.
    """
    for sub in ["sections", "snippets"]:
        base = theme / sub
        if not base.is_dir():
            continue
        for path in base.rglob("*.liquid"):
            text = blank_liquid_comments(path.read_text(encoding="utf-8"))
            for m in IMAGE_TAG_ARGS_RE.finditer(text):
                args = m.group(1)
                if re.search(r"\|\s*\w", args):
                    line = text.count("\n", 0, m.start()) + 1
                    warnings.append(
                        f"{path.relative_to(theme)}:{line}: a filter is piped inside an "
                        f"image_tag argument. Liquid applies it to the whole tag (and "
                        f"`| escape` raises LiquidHTMLSyntaxError). Pre-compute the value "
                        f"into an {{% assign %}} and pass the plain variable. [reliability #5]"
                    )


def check_custom_element_display(theme: Path) -> None:
    """Reliability §7: every custom element needs an explicit display in CSS.

    WARNING — collects tag names from customElements.define(...) across assets/*.js
    and checks that *some* CSS/style declares `<tag> { ... display ... }`."""
    tags: set[str] = set()
    assets = theme / "assets"
    if assets.is_dir():
        for path in assets.glob("*.js"):
            for m in CUSTOM_ELEMENT_RE.finditer(path.read_text(encoding="utf-8")):
                tags.add(m.group(1))
    if not tags:
        return
    # Gather all CSS text (base.css + any {% style %} blocks in sections/snippets).
    css_text = []
    for path in assets.rglob("*.css"):
        css_text.append(path.read_text(encoding="utf-8"))
    for sub in ["sections", "snippets", "layout"]:
        base = theme / sub
        if base.is_dir():
            for path in base.rglob("*.liquid"):
                css_text.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(css_text)
    for tag in sorted(tags):
        # crude: does a selector mention the tag and a display within ~120 chars?
        pat = re.compile(re.escape(tag) + r"[^{}]*\{[^{}]*display\s*:", re.DOTALL)
        if not pat.search(blob):
            warnings.append(
                f"custom element <{tag}> is defined in JS but no CSS rule sets its "
                f"`display`. Custom elements default to display:inline, so padding/"
                f"height are ignored (collapsed layout). Add `{tag} {{ display: block }}`. "
                f"[reliability #7]"
            )


def check_cruft(theme: Path) -> None:
    """Reliability §14: no stray files, and flat asset/snippet/section dirs."""
    for path in theme.rglob("*"):
        rel = path.relative_to(theme)
        parts = rel.parts
        name = path.name
        if name in CRUFT_NAMES or path.suffix in CRUFT_SUFFIXES:
            errors.append(
                f"Cruft in theme: {rel} — must not ship inside a theme "
                f"(importer rejection / bloat). Delete before packaging. [reliability #14]"
            )
        # Flat-dir rule: no subfolders anywhere under assets/snippets/sections.
        if len(parts) >= 2 and parts[0] in FLAT_DIRS and path.is_dir():
            errors.append(
                f"Nested folder not allowed: {rel}/ — {parts[0]}/ must be flat. "
                f"[shopify-standards #1]"
            )
    # templates/ may only nest under customers/ or metaobject/
    templates = theme / "templates"
    if templates.is_dir():
        for path in templates.rglob("*"):
            if path.is_dir():
                rel = path.relative_to(theme).as_posix()
                if rel not in FLAT_DIR_EXCEPTIONS and not any(
                    rel.startswith(e + "/") for e in FLAT_DIR_EXCEPTIONS
                ):
                    warnings.append(
                        f"Unexpected subfolder in templates/: {rel}/ — only "
                        f"customers/ and metaobject/ are allowed."
                    )


# ---------------------------------------------------------------------------


def main() -> int:
    # Never crash on our own non-ASCII output when stdout is a Windows pipe
    # (cp1252). Force UTF-8 with replacement so the tool is reliable everywhere.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    theme = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(f"Validating theme at: {theme}\n")

    locale = load_schema_locale(theme)

    # structural
    check_structure(theme)
    check_json_files(theme)
    available = check_section_schemas(theme, locale)
    check_template_references(theme, available)
    check_settings_schema(theme)

    # import / sync landmines
    check_stylesheet_tags(theme)
    check_layout_static_sections(theme)
    check_image_tag_filters(theme)
    check_custom_element_display(theme)
    check_cruft(theme)

    for w in warnings:
        print(f"  ! WARNING  {w}")
    for e in errors:
        print(f"  x ERROR    {e}")

    print()
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        print("Fix these, then run `shopify theme check` for full validation.")
        print("Landmine details: references/reliability-and-sync.md")
        return 1
    print(f"PASSED structural + landmine checks ({len(warnings)} warning(s)).")
    print("Now run `shopify theme check` for full Shopify validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
