#!/usr/bin/env python3
"""
validate_theme.py — fast structural sanity check for an Online Store 2.0 theme.

This is NOT a replacement for `shopify theme check` (run that too). It catches the
mistakes that most often slip through generation:

  * malformed JSON in templates, section groups, config, and locales
  * malformed JSON inside a section's {% schema %} block
  * missing required directories / files / templates
  * JSON templates that reference a section `type` with no matching section file
  * sections missing a {% schema %} entirely

Usage:
    python scripts/validate_theme.py [THEME_DIR]

THEME_DIR defaults to the current directory. Exit code 0 = clean, 1 = problems.
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

SCHEMA_RE = re.compile(r"{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}", re.DOTALL)

errors: list[str] = []
warnings: list[str] = []


def strip_json_comments(text: str) -> str:
    """Remove // and /* */ comments that live outside string literals (Shopify
    permits these in JSON templates / section groups / config files)."""
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


def check_section_schemas(theme: Path) -> dict[str, Path]:
    """Validate {% schema %} JSON and return the set of available section types."""
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
            json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid schema JSON in sections/{path.name} -> {exc}")
    # Section-group JSON files also provide types indirectly; note their existence.
    for path in sections.glob("*.json"):
        available[path.stem] = path
    return available


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


def main() -> int:
    theme = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(f"Validating theme at: {theme}\n")

    check_structure(theme)
    check_json_files(theme)
    available = check_section_schemas(theme)
    check_template_references(theme, available)
    check_settings_schema(theme)

    for w in warnings:
        print(f"  ! WARNING  {w}")
    for e in errors:
        print(f"  x ERROR    {e}")

    print()
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        print("Fix these, then run `shopify theme check` for full validation.")
        return 1
    print(f"PASSED structural checks ({len(warnings)} warning(s)).")
    print("Now run `shopify theme check` for full Shopify validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
