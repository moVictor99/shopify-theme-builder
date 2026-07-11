#!/usr/bin/env python3
"""
selftest.py — "bomb test" for validate_theme.py.

Proves the reliability linter actually catches each import/sync landmine. It:
  1. copies the bundled skeleton (assets/theme-skeleton) to a temp dir,
  2. confirms the pristine skeleton passes clean (exit 0, no errors),
  3. for each landmine, injects it into a FRESH copy, runs validate_theme.py, and
     asserts the expected error/warning is reported (and exit code is right).

Run:  python scripts/selftest.py
Exit: 0 = all guards fire correctly, 1 = a guard failed to catch its landmine.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
SKELETON = HERE.parent / "assets" / "theme-skeleton"
VALIDATOR = HERE / "validate_theme.py"


def run_validator(theme: Path) -> tuple[int, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(theme)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def fresh_copy() -> Path:
    dst = Path(tempfile.mkdtemp(prefix="stb-bomb-")) / "theme"
    shutil.copytree(SKELETON, dst)
    return dst


# --- landmine injectors: each mutates a fresh theme copy in place -----------

def inject_stylesheet_tag(theme: Path) -> None:
    p = theme / "sections" / "rich-text.liquid"
    p.write_text(p.read_text(encoding="utf-8") + "\n{% stylesheet %}\n.x{color:red}\n{% endstylesheet %}\n", encoding="utf-8")


def inject_javascript_tag(theme: Path) -> None:
    p = theme / "sections" / "rich-text.liquid"
    p.write_text(p.read_text(encoding="utf-8") + "\n{% javascript %}\nconsole.log(1)\n{% endjavascript %}\n", encoding="utf-8")


def inject_long_block_name(theme: Path) -> None:
    p = theme / "sections" / "main-product.liquid"
    t = p.read_text(encoding="utf-8")
    # "Title" (5) -> a 26-char name
    t = t.replace('{ "type": "title", "name": "Title", "limit": 1 }',
                  '{ "type": "title", "name": "Title of exactly twentysix!!", "limit": 1 }')
    p.write_text(t, encoding="utf-8")


def inject_bad_role_key(theme: Path) -> None:
    p = theme / "config" / "settings_schema.json"
    t = p.read_text(encoding="utf-8")
    t = t.replace('"icons": "text"', '"icons": "text",\n          "shadow": "text"')
    p.write_text(t, encoding="utf-8")


def inject_static_section_in_layout(theme: Path) -> None:
    p = theme / "layout" / "theme.liquid"
    t = p.read_text(encoding="utf-8")
    t = t.replace("</body>", "  {% section 'rich-text' %}\n  </body>")
    p.write_text(t, encoding="utf-8")


def inject_image_tag_filter(theme: Path) -> None:
    p = theme / "snippets" / "responsive-image.liquid"
    p.write_text(
        "{{ img | image_url: width: 400 | image_tag: alt: img.alt | escape }}\n",
        encoding="utf-8",
    )


def inject_cruft(theme: Path) -> None:
    (theme / "npm-cache").mkdir()
    (theme / "npm-cache" / "junk.txt").write_text("x", encoding="utf-8")
    (theme / "debug.log").write_text("x", encoding="utf-8")


def inject_missing_custom_element_display(theme: Path) -> None:
    p = theme / "assets" / "base.css"
    t = p.read_text(encoding="utf-8")
    t = t.replace("header-nav, cart-drawer { display: block; }", "")
    p.write_text(t, encoding="utf-8")


def inject_nested_asset_dir(theme: Path) -> None:
    (theme / "assets" / "vendor").mkdir()
    (theme / "assets" / "vendor" / "lib.js").write_text("//x", encoding="utf-8")


# name, injector, expected substring, must_error(True=exit1)
CASES = [
    ("#1 {% stylesheet %} tag",        inject_stylesheet_tag,               "stylesheet %} tag",              True),
    ("#1 {% javascript %} tag",        inject_javascript_tag,               "javascript %} tag",             True),
    ("#2 block name > 25 chars",       inject_long_block_name,              "chars (> 25)",                  True),
    ("#3 invalid color role key",      inject_bad_role_key,                 "invalid key(s) ['shadow']",     True),
    ("#4 static section in layout",    inject_static_section_in_layout,     "static {% section",             True),
    ("#5 filter inside image_tag",     inject_image_tag_filter,             "image_tag argument",            False),
    ("#14 cruft in theme root",        inject_cruft,                        "Cruft in theme",                True),
    ("#14 nested asset subfolder",     inject_nested_asset_dir,             "must be flat",                  True),
    ("#7 custom element no display",   inject_missing_custom_element_display, "default to display:inline",   False),
]


def main() -> int:
    if not SKELETON.is_dir():
        print(f"skeleton not found: {SKELETON}")
        return 1

    print("== baseline: pristine skeleton must pass clean ==")
    base = fresh_copy()
    code, out = run_validator(base)
    shutil.rmtree(base.parent, ignore_errors=True)
    ok_base = code == 0 and "x ERROR" not in out
    print(f"  {'PASS' if ok_base else 'FAIL'}  pristine skeleton -> exit {code}")
    if not ok_base:
        print(out)

    print("\n== bomb test: each landmine must be caught ==")
    results = [ok_base]
    for name, inject, expected, must_error in CASES:
        theme = fresh_copy()
        try:
            inject(theme)
            code, out = run_validator(theme)
        finally:
            shutil.rmtree(theme.parent, ignore_errors=True)
        caught = expected in out
        exit_ok = (code == 1) if must_error else True
        passed = caught and exit_ok
        results.append(passed)
        tag = "PASS" if passed else "FAIL"
        detail = "" if passed else f"  (exit={code}, expected {expected!r} in output)"
        print(f"  {tag}  {name}{detail}")
        if not passed:
            print("    --- validator output ---")
            print("    " + out.replace("\n", "\n    "))

    total, good = len(results), sum(results)
    print(f"\n{good}/{total} guards fired correctly.")
    return 0 if good == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
