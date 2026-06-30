#!/usr/bin/env python3
"""
Nerdify — TTF/OTF to WOFF2 conversion script.

Converts every .ttf/.otf font in `fonts-source/` into a .woff2 file in
`src/fonts/`, then regenerates `src/fonts.css` with an @font-face rule
for every converted font and `src/popup/popup.html` with a font-picker
button for each one. Run this whenever you add, remove, or change the
fonts in fonts-source/.

Usage:
    python scripts/build_fonts.py

Requirements:
    pip install fonttools brotli

Folder layout expected:
    nerdify/
      fonts-source/       <- drop your .ttf / .otf Nerd Font files here
      src/
        fonts/            <- generated .woff2 files (overwritten each run)
        fonts.css         <- generated @font-face rules (overwritten each run)
        popup/
          popup.html      <- font-option buttons are regenerated in-place
"""

import re
import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("Missing dependency. Install with:")
    print("    pip install fonttools brotli")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "fonts-source"
OUTPUT_FONT_DIR = ROOT / "src" / "fonts"
FONTS_CSS_PATH = ROOT / "src" / "fonts.css"
POPUP_HTML_PATH = ROOT / "src" / "popup" / "popup.html"

SUPPORTED_EXTENSIONS = {".ttf", ".otf"}

# A few sample glyphs from the Nerd Fonts private-use range, used purely
# as a visual preview inside each font-picker button in the popup.
PREVIEW_GLYPHS = "\ue7b5 \uf02d \uf126"


def slugify(name: str) -> str:
    """Turn a font family name into a lowercase storage key, e.g.
    'JetBrainsMono Nerd Font Mono' -> 'jetbrainsmononerdfontmono'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def read_family_name(font: "TTFont", fallback: str) -> str:
    """Pull the human-readable family name out of the font's own name
    table (nameID 16 'Typographic Family', falling back to nameID 1
    'Font Family'). This is far more reliable than guessing from the
    filename, since Nerd Fonts filenames vary a lot release to release."""
    name_table = font["name"]
    for name_id in (16, 1):
        for plat_id, enc_id, lang_id in ((3, 1, 0x409), (1, 0, 0)):
            rec = name_table.getName(name_id, plat_id, enc_id, lang_id)
            if rec:
                value = rec.toUnicode().strip()
                if value:
                    return value
    return fallback


def css_font_family(family_name: str) -> str:
    """The font-family name written into @font-face / used by the page.
    Avoids duplicating 'Nerd Font' if the font's own name already has it."""
    if "nerd font" in family_name.lower():
        return family_name
    return f"{family_name} Nerd Font"


def convert_to_woff2(src_path: Path, dest_path: Path, fallback_name: str):
    font = TTFont(src_path)
    family_name = read_family_name(font, fallback_name)
    font.flavor = "woff2"
    font.save(str(dest_path))
    size = dest_path.stat().st_size
    return family_name, size


def find_source_fonts():
    if not SOURCE_DIR.exists():
        print(f"Source folder not found: {SOURCE_DIR}")
        print("Create it and drop your .ttf/.otf Nerd Font files inside.")
        sys.exit(1)

    fonts = sorted(
        p for p in SOURCE_DIR.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not fonts:
        print(f"No .ttf/.otf files found in {SOURCE_DIR}")
        print("Drop some Nerd Font files in there and run this again.")
        sys.exit(1)

    return fonts


def clean_output_dir():
    OUTPUT_FONT_DIR.mkdir(parents=True, exist_ok=True)
    for existing in OUTPUT_FONT_DIR.glob("*.woff2"):
        existing.unlink()


def build_fonts_css(entries):
    """entries: list of (slug, family_name, woff2_filename)"""
    blocks = ["/* Nerdify — bundled font declarations (auto-generated, do not edit by hand) */", ""]

    for _slug, family_name, woff2_filename in entries:
        blocks.append(
            "@font-face {\n"
            f'  font-family: "{family_name}";\n'
            f'  src: url("fonts/{woff2_filename}") format("woff2");\n'
            "  font-weight: normal;\n"
            "  font-style: normal;\n"
            "  font-display: swap;\n"
            "}\n"
        )

    default_family = entries[0][1] if entries else "monospace"

    blocks.append(
        "/* Applied/removed dynamically by content.js via these marker classes */\n"
        "\n"
        "html.nf-active-all,\n"
        "html.nf-active-all * {\n"
        f'  font-family: var(--nf-font-family, "{default_family}"), monospace !important;\n'
        "}\n"
        "\n"
        "html.nf-active-code pre,\n"
        "html.nf-active-code code,\n"
        "html.nf-active-code kbd,\n"
        "html.nf-active-code samp,\n"
        "html.nf-active-code pre *,\n"
        "html.nf-active-code code *,\n"
        "html.nf-active-code textarea[class*=\"code\"],\n"
        "html.nf-active-code .CodeMirror,\n"
        "html.nf-active-code .cm-editor,\n"
        "html.nf-active-code .monaco-editor,\n"
        "html.nf-active-code .monaco-editor * {\n"
        f'  font-family: var(--nf-font-family, "{default_family}"), monospace !important;\n'
        "}\n"
    )

    FONTS_CSS_PATH.write_text("\n".join(blocks), encoding="utf-8")


def build_font_map_js(entries):
    """Returns a JS object literal string for content.js / popup.js FONT_MAP."""
    lines = ["{"]
    for slug, family_name, _woff2_filename in entries:
        lines.append(f'  {slug}: "{family_name}",')
    lines.append("}")
    return "\n".join(lines)


def update_content_js(entries):
    content_js_path = ROOT / "src" / "content.js"
    text = content_js_path.read_text(encoding="utf-8")

    new_map = build_font_map_js(entries)
    text = re.sub(
        r"const FONT_MAP = \{.*?\};",
        f"const FONT_MAP = {new_map};",
        text,
        count=1,
        flags=re.DOTALL,
    )

    default_slug = entries[0][0] if entries else "default"
    text = re.sub(
        r'(const DEFAULTS = \{.*?\bfont:\s*)"[^"]*"',
        rf'\1"{default_slug}"',
        text,
        count=1,
        flags=re.DOTALL,
    )

    content_js_path.write_text(text, encoding="utf-8")


def update_popup_html(entries):
    text = POPUP_HTML_PATH.read_text(encoding="utf-8")

    buttons = []
    for slug, family_name, _woff2_filename in entries:
        label = family_name.replace(" Nerd Font", "")
        buttons.append(
            f'        <button class="font-option" data-font="{slug}" style="font-family:\'{family_name}\'">\n'
            f'          <span class="font-glyphs">{PREVIEW_GLYPHS}</span>\n'
            f'          <span class="font-name">{label}</span>\n'
            f"        </button>"
        )

    new_list_inner = "\n".join(buttons)
    text = re.sub(
        r'(<div class="font-list" id="fontList">\n)(.*?)(\n      </div>)',
        lambda m: m.group(1) + new_list_inner + m.group(3),
        text,
        count=1,
        flags=re.DOTALL,
    )

    POPUP_HTML_PATH.write_text(text, encoding="utf-8")


def update_popup_js_default(entries):
    popup_js_path = ROOT / "src" / "popup" / "popup.js"
    text = popup_js_path.read_text(encoding="utf-8")
    default_slug = entries[0][0] if entries else "default"
    text = re.sub(
        r'(const DEFAULTS = \{.*?\bfont:\s*)"[^"]*"',
        rf'\1"{default_slug}"',
        text,
        count=1,
        flags=re.DOTALL,
    )
    popup_js_path.write_text(text, encoding="utf-8")


def main():
    sources = find_source_fonts()
    clean_output_dir()

    print(f"Found {len(sources)} font file(s) in {SOURCE_DIR}\n")

    entries = []
    seen_slugs = {}
    for src_path in sources:
        fallback = re.sub(r"-(Regular|Bold|Italic|BoldItalic)$", "", src_path.stem, flags=re.I)

        # Read family name first (cheap), then decide final paths before saving.
        probe_font = TTFont(src_path)
        raw_family = read_family_name(probe_font, fallback)
        family_name = css_font_family(raw_family)
        slug = slugify(raw_family)

        # Guard against two different source files producing the same slug
        # (e.g. Regular + Bold of the same family both present).
        if slug in seen_slugs:
            seen_slugs[slug] += 1
            slug = f"{slug}{seen_slugs[slug]}"
        else:
            seen_slugs[slug] = 0

        woff2_filename = f"{slug}.woff2"
        dest_path = OUTPUT_FONT_DIR / woff2_filename

        _family_name_confirmed, size = convert_to_woff2(src_path, dest_path, fallback)
        print(f"  {src_path.name:45s} -> fonts/{woff2_filename}  ({size // 1024} KB)  family=\"{family_name}\"")

        entries.append((slug, family_name, woff2_filename))

    build_fonts_css(entries)
    update_content_js(entries)
    update_popup_html(entries)
    update_popup_js_default(entries)

    print(f"\nDone. {len(entries)} font(s) converted and wired up:")
    print(f"  - {FONTS_CSS_PATH.relative_to(ROOT)}")
    print(f"  - src/content.js (FONT_MAP)")
    print(f"  - src/popup/popup.html (font picker buttons)")
    print(f"  - src/popup/popup.js (default font)")
    print("\nReload the unpacked extension in your browser to see the changes.")


if __name__ == "__main__":
    main()
