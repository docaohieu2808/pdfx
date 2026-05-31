---
name: pdfx
description: Complete one-call PDF toolkit. GENERATE publication-quality PDFs/ebooks from Markdown (AI cover, auto TOC + depth-2 sub-entries, part dividers, A-Z index, syntax-highlighted code, inline SVG + Mermaid diagrams, auto-preview) AND PROCESS any PDF — merge/split/rotate/pages/nup/crop, compress, linearize, PDF/A, repair, encrypt/decrypt/unlock/redact/permissions, watermark/stamp/metadata, extract text/tables/images/fonts/links/attachments/bookmarks, to-images/html/markdown, from-images/html/url, OCR + searchable OCR, compare(diff), fill forms. Self-contained.
author: hieudc
license: MIT
---

# pdfx — complete PDF toolkit

One skill for **anything PDF**, two pillars: **(A) Generate** beautiful PDFs from Markdown,
**(B) Process** existing PDFs (35 subcommands). Self-contained: bundled fonts, runnable CLI
scripts, reference guides. Set the env once:

```bash
PDFX=/path/to/pdfx          # wherever this skill is installed
PY="$HOME/.claude/skills/.venv/bin/python3"   # or any venv with the deps below
```

## Decide which pillar
| You want to… | Pillar | Entry |
|--------------|--------|-------|
| Make an ebook/handbook/report/whitepaper | **A. Generate** | `build_ebook_from_markdown.py` |
| Anything to an existing PDF (transform/extract/secure/convert/analyze) | **B. Process** | `pdf_process.py <cmd>` |
| Fill a PDF form | **B. Forms** | `check_fillable_fields.py` → `fill_fillable_fields.py` |

---

## A. Generate beautiful PDFs / ebooks
Pipeline: `Markdown → HTML (python-markdown + Pygments) → WeasyPrint → PDF`. Published-grade
print CSS: `@page` running headers/footers, `target-counter` TOC page numbers, dot leaders,
`bookmark-level` PDF outline, `@font-face`.

```bash
$PY "$PDFX/scripts/build_ebook_from_markdown.py" \
    --title "DevOps Handbook" --subtitle "Complete Reference" \
    --stats "32 CHAPTERS · 5 PARTS" \
    --gen-cover "isometric servers and data-flow lines, blue tech" \
    --parts "1=Foundations,7=Build & Ship,14=Infrastructure" \
    --toc-depth 2 --index --preview \
    --page a4 --theme light --accent "#2563eb" \
    --output handbook.pdf  ch01.md ch02.md ...
```

Each file's first `# H1` = chapter title (removed from body). `--input-dir DIR` takes all `*.md` sorted.

**Options:** `--gen-cover "<idea>"` (AI cover via Gemini, 2:3/2K, text-free) · `--cover-image <file>` ·
`--page a4|6x9` · `--theme light|dark` · `--accent "#hex"` · `--kicker` · `--stats` ·
`--parts "N=Title,…"` (full-page part divider before chapter N) · `--toc-depth 1|2` (2 = list H2s) ·
`--index` (A-Z back-of-book index) · `--preview` (auto-render page PNGs to `<out>_preview/`).

**Diagrams (two ways, both render in WeasyPrint):**
- **Inline SVG** — write `<svg>…</svg>` straight in the Markdown. Hand-authored SVG is the most
  reliable, offline, pixel-perfect option. (pdfx shields `<svg>` from the `md_in_html` extension,
  so inline SVG no longer gets mangled.)
- **Mermaid** — a ```` ```mermaid ```` fenced block is auto-rendered to SVG (via `mmdc`/`npx
  @mermaid-js/mermaid-cli`; Chromium auto-downloads on first use). Uses `htmlLabels:false` so labels
  are real `<text>` WeasyPrint can draw. If no renderer is available the block degrades to a code
  listing (build still succeeds).

**A-Z index** auto-collects every term that is a **bold first table cell** (`| **Term** | … |`) plus
explicit `[[Term]]` markers, mapping each to its chapter number(s). Perfect for glossary handbooks.

**Always visually validate** (compiles ≠ looks right): use `--preview` then Read the PNGs, or
`pdftoppm -png -r 150 -f 1 -l 1 handbook.pdf prev`. Recipes: `references/weasyprint-recipes.md`.

---

## B. Process existing PDFs — `pdf_process.py <cmd>`
`$PY "$PDFX/scripts/pdf_process.py" -h` lists everything. Grouped:

### Transform (structure)
| Command | Example |
|---------|---------|
| `merge` | `pdf_process.py merge out.pdf a.pdf b.pdf …` |
| `split` | `pdf_process.py split in.pdf --ranges "1-3,4-6" --out-dir DIR` |
| `rotate` | `pdf_process.py rotate in.pdf out.pdf --angle 90 [--pages 1,2]` |
| `pages` | `pdf_process.py pages in.pdf out.pdf --keep "3,1,2"` / `--remove "4,5"` (keep also reorders) |
| `nup` | `pdf_process.py nup in.pdf out.pdf --n 2` (2/4 pages per sheet) |
| `crop` | `pdf_process.py crop in.pdf out.pdf --margins "5,5,5,5"` (top,right,bottom,left %) |

### Extract / convert-out
| Command | Example |
|---------|---------|
| `extract-text` | `… extract-text in.pdf [--out t.txt] [--layout]` |
| `extract-tables` | `… extract-tables in.pdf [--out t.csv]` |
| `extract-images` | `… extract-images in.pdf --out-dir DIR` (embedded rasters) |
| `to-images` | `… to-images in.pdf --out-dir DIR [--dpi 150] [--fmt png|jpeg]` |
| `to-html` | `… to-html in.pdf [--out o.html]` |
| `to-markdown` | `… to-markdown in.pdf [--out o.md]` |
| `fonts` | `… fonts in.pdf` (embedded fonts) |
| `links` | `… links in.pdf` (hyperlinks) |
| `attachments` | `… attachments in.pdf [--save --out-dir DIR]` |
| `bookmarks` | `… bookmarks in.pdf` (outline) |

### Security
| Command | Example |
|---------|---------|
| `encrypt` / `decrypt` | `… encrypt in.pdf out.pdf --password PW [--owner PW]` |
| `unlock` | `… unlock in.pdf out.pdf [--password PW]` (strip print/copy restrictions, qpdf) |
| `redact` | `… redact in.pdf out.pdf --text "SECRET"` or `--rects "1:x0,y0,x1,y1"` (true removal) |
| `permissions` | `… permissions in.pdf [--password PW]` (inspect flags) |

### Optimize
| Command | Example |
|---------|---------|
| `compress` | `… compress in.pdf out.pdf --quality screen|ebook|printer|prepress` |
| `linearize` | `… linearize in.pdf out.pdf` (fast web view) |
| `pdfa` | `… pdfa in.pdf out.pdf` (archival PDF/A-2b) |
| `repair` | `… repair in.pdf out.pdf` (rebuild broken/bloated) |

### Annotate / info
| Command | Example |
|---------|---------|
| `watermark` | `… watermark in.pdf out.pdf --text "DRAFT" [--opacity 0.12]` |
| `stamp` | `… stamp in.pdf out.pdf --text "Page {page}/{pages}" --pos footer-center` |
| `metadata` | `… metadata in.pdf [--set Title=… --output out.pdf \| --in-place]` |

### Convert-in (create from other formats)
| Command | Example |
|---------|---------|
| `from-images` | `… from-images out.pdf a.png b.jpg …` (lossless, img2pdf) |
| `from-html` | `… from-html page.html out.pdf` |
| `from-url` | `… from-url https://example.com out.pdf` (needs network) |

### Analyze
| Command | Example |
|---------|---------|
| `info` | `… info in.pdf [--password PW]` (pages, size, fonts, metadata, encryption) |
| `compare` | `… compare a.pdf b.pdf [--out-dir DIR] [--dpi 100]` (page-by-page visual diff) |

### OCR (scanned PDFs) — two engines
| Command | Example |
|---------|---------|
| `ocr` | `… ocr scan.pdf --lang vie --engine auto [--out t.txt] [--dpi 300]` (extract text) |
| `ocr-searchable` | `… ocr-searchable scan.pdf out.pdf --lang vie` (add selectable text layer) |

`--engine auto` (default) uses **Gemini** (`gemini-2.5-flash`, needs `GEMINI_API_KEY`) for
Vietnamese — far more reliable on real scans and preserves diacritics — else falls back to
**tesseract** (offline). Force with `--engine tesseract|gemini`. **Model** (`--model`, default
`gemini-2.5-flash` = GA/fast/cheap/accurate): hardest scans → `gemini-3.5-flash` or
`gemini-3-flash-preview` (#1 OCR Arena); cheapest bulk → `gemini-2.5-flash-lite` (risk: drops words
on noisy docs). Avoid pro (slow, no gain) / `gemini-2.0*` (deprecated). See
`references/gemini-ocr-model-comparison.md`. ⚠ Plain tesseract with the default `--lang eng` MANGLES Vietnamese diacritics
("Việt"→"Viet"); for Vietnamese always pass `--lang vie` (tesseract) or use `auto`/`gemini`.
`ocr-searchable` is tesseract-only (an LLM can't position glyphs) — pass `--lang vie` for VN.

### Forms (separate scripts — run check first)
`check_fillable_fields.py in.pdf` → `fill_fillable_fields.py in.pdf fields.json out.pdf`.
Non-fillable forms: `fill_pdf_form_with_annotations.py`. Inspect: `extract_form_field_info.py`,
`check_bounding_boxes.py`. Guide: `references/forms.md`.

---

## Setup / install (self-contained — depends on NO other skill)
1. **Copy the whole `pdfx/` folder** to any skills dir. Everything bundles: scripts, `pdfx_ops/`,
   `pdfx_lib/`, references, `assets/fonts/`.
2. **Set `PDFX`** + a `PY` venv (above).
3. **Python deps:**
   ```bash
   pip install weasyprint markdown pygments pypdf pikepdf pymupdf pdfplumber \
       reportlab img2pdf pytesseract pdf2image google-genai
   ```
4. **System tools:** `qpdf`, `ghostscript` (compress/pdfa), `poppler-utils` (pdfinfo/pdftoppm/
   pdfimages/pdffonts/pdftohtml/pdfdetach), `mupdf-tools` (repair), `img2pdf`, `tesseract-ocr`
   (+ `tesseract-ocr-vie`), and WeasyPrint's Pango/cairo. Mermaid (optional): `node`/`npx`.
5. **Optional** — AI covers: `GEMINI_API_KEY` in env or `$PDFX/.env` / `~/.claude/.env`. Without it
   `--gen-cover` falls back to a gradient cover.

Each capability degrades gracefully: a missing tool gives a clear hint, never a silent bad output.

## Files
- `scripts/build_ebook_from_markdown.py` — ebook generator (orchestrates `pdfx_lib/`).
- `scripts/pdfx_lib/` — `cover.py` (AI cover), `mermaid.py` (diagram render), `markdown_render.py`
  (chapters, inline-SVG protection, badges, heading ids), `toc_index.py` (TOC + index + parts),
  `styles.py` (print CSS).
- `scripts/pdf_process.py` — thin dispatcher over `pdfx_ops/`.
- `scripts/pdfx_ops/` — `transform.py · extract.py · security.py · optimize.py · annotate.py ·
  convert.py · analyze.py · ocr_ops.py` (+ `_util.py`).
- `scripts/{check_fillable_fields,fill_fillable_fields,fill_pdf_form_with_annotations,
  extract_form_field_info,check_bounding_boxes,convert_pdf_to_images,create_validation_image}.py` — forms.
- `references/` — `weasyprint-recipes.md`, `pdf-manipulation-guide.md`, `forms.md`,
  `ocr-extraction-patterns.md`, `reference.md`. `assets/fonts/` — display fonts. `examples/` — smoke-test chapters.

## Smoke test
```bash
$PY "$PDFX/scripts/build_ebook_from_markdown.py" --title "pdfx smoke" --input-dir "$PDFX/examples" --output /tmp/pdfx.pdf --preview
$PY "$PDFX/scripts/pdf_process.py" info /tmp/pdfx.pdf
$PY "$PDFX/scripts/pdf_process.py" compress /tmp/pdfx.pdf /tmp/pdfx-small.pdf --quality ebook
```
