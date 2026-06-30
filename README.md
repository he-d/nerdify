# Nerdify

A browser extension that renders the current website using a Nerd Font of
your choice. Works unmodified in Chrome, Edge, and Brave, since all three
support Manifest V3 Chrome extensions natively.

## Project layout

```
nerdify/
  fonts-source/        Drop your .ttf / .otf Nerd Font files here
  scripts/
    build_fonts.py      Converts fonts-source/*.ttf -> src/fonts/*.woff2
                         and regenerates fonts.css, content.js, and
                         popup.html to match
  src/                  The actual extension (load this folder unpacked)
    manifest.json
    background.js
    content.js
    fonts.css            auto-generated, do not edit by hand
    fonts/               auto-generated .woff2 files
    icons/
    popup/
      popup.html         font-picker buttons auto-generated in place
      popup.css
      popup.js
```

## Setup

1. Put your Nerd Font `.ttf`/`.otf` files into `fonts-source/`. This zip
   already ships with 5 example fonts in there (JetBrainsMono, FiraCode,
   Hack, CaskaydiaCove, MesloLGL) so the script has something to run on
   out of the box — swap them out for your own files from your
   `nerdfonts` folder whenever you're ready; the script picks up
   whatever `.ttf`/`.otf` files it finds, however many there are.
2. Install the conversion script's dependency:
   ```
   pip install fonttools brotli
   ```
3. Run the build script from the project root:
   ```
   python scripts/build_fonts.py
   ```
   This converts every font in `fonts-source/` to `.woff2`, writes them
   into `src/fonts/`, and regenerates `src/fonts.css`, the `FONT_MAP` in
   `src/content.js`, and the font-picker buttons in
   `src/popup/popup.html` — all pulling each font's real family name
   from its own internal name table, so naming stays accurate no matter
   how the source files are named.
4. Re-run the script any time you add, remove, or swap fonts in
   `fonts-source/`. It's safe to run repeatedly — it fully regenerates
   the derived files each time rather than appending to them. The
   generated `.woff2` files in `src/fonts/` are committed to the repo,
   so the extension works immediately after a fresh clone without
   needing to run the script first.

## Load the extension (Developer Mode — same flow for all three browsers)

### Chrome
1. Go to `chrome://extensions`
2. Toggle **Developer mode** on (top right)
3. Click **Load unpacked**
4. Select the `nerdify/src` folder

### Edge
1. Go to `edge://extensions`
2. Toggle **Developer mode** on (left sidebar)
3. Click **Load unpacked**
4. Select the `nerdify/src` folder

### Brave
1. Go to `brave://extensions`
2. Toggle **Developer mode** on (top right)
3. Click **Load unpacked**
4. Select the `nerdify/src` folder

After loading, pin the extension icon to your toolbar. Whenever you
re-run `build_fonts.py`, click the reload icon on the extension's card
in the browser's extensions page to pick up the changes.

## Usage

Click the extension icon to open the popup:

- **global** — flips the font override on/off across all sites
- **this site** — overrides the global setting just for the current
  domain (`Inherit` follows the global toggle, `Force on`/`Force off`
  pin it regardless of the global setting)
- **scope** — `All text` rewrites every element's font; `Code only`
  restricts it to code blocks and editor widgets (`pre`, `code`, `kbd`,
  `samp`, CodeMirror, Monaco)
- **font** — pick which bundled Nerd Font to use; each option previews
  itself in its own font

Settings sync via `chrome.storage.sync`, so they follow you across
devices signed into the same browser profile. Changes apply immediately
to open tabs.

## Notes on what to expect

Nerd Fonts are patched **monospace** coding fonts. Applying one to an
ordinary website (news articles, blogs, etc.) will make all text
monospaced — readable, but stylistically different from the site's
intended typography. It tends to look most natural on code-heavy pages
like GitHub, documentation sites, or Stack Overflow, which is also why
the "Code only" scope exists.

The special icon glyphs Nerd Fonts are known for (file type icons, git
symbols, etc.) only render where the page's actual text already
contains those specific Unicode codepoints — switching the font does
not inject new icons into existing page content, it just changes how
existing characters are drawn.

## License

Nerd Fonts are typically distributed under the SIL Open Font License.
If you're bundling fonts from the official Nerd Fonts project
(https://github.com/ryanoasis/nerd-fonts) or another OFL-licensed
source, that license carries over to the generated `.woff2` files in
`src/fonts/`. Check the license of whatever fonts you drop into
`fonts-source/` before distributing this extension publicly.
