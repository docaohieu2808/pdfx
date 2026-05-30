---
name: pdfx
description: Complete PDF toolkit — BOTH generate publication-quality PDFs/ebooks from Markdown (designed cover with AI art, auto-numbered TOC, syntax-highlighted code, typography) AND process existing PDFs (OCR, extract text/tables, merge, split, rotate, watermark, encrypt/decrypt, metadata, fill forms, render to images). One self-contained skill for any PDF task — generation and processing.
author: hieudc
license: MIT
---

# pdfx — complete PDF toolkit

One skill, two pillars: **(A) Generate** beautiful PDFs/ebooks from Markdown, and
**(B) Process** existing PDFs (extract / transform / fill). Self-contained: bundled fonts,
runnable CLI scripts, and reference guides. Point `PDFX` at the folder wherever this skill
is installed, then use any Python environment with the dependencies installed:

```bash
PDFX=/path/to/pdfx
PY=python
```

## Decide which pillar
| You want to… | Go to | Tool |
|--------------|-------|------|
| Make a gorgeous ebook/handbook/report/whitepaper | **A. Generate** | `scripts/build_ebook_from_markdown.py` |
| Pull text/tables out of a PDF, OCR a scan | **B. Process** | `scripts/pdf_process.py extract-text\|extract-tables\|ocr` |
| Merge/split/rotate/watermark/encrypt/metadata | **B. Process** | `scripts/pdf_process.py <cmd>` |
| Fill a PDF form | **B. Process** | `scripts/check_fillable_fields.py` → `fill_fillable_fields.py` |
| Render PDF pages to PNG (visual check) | **B. Process** | `scripts/pdf_process.py to-images` |

---

## A. Generate beautiful PDFs / ebooks
Pipeline: `Markdown -> HTML (python-markdown + Pygments) -> WeasyPrint -> PDF`. WeasyPrint
gives published-grade print CSS: `@page`, running header/footer, `target-counter` (TOC page
numbers), `leader()` (dot leaders), `bookmark-level` (PDF outline), `@font-face`.

```bash
# AI-generate the cover in the same command (Gemini Nano Banana, free-tier key)
$PY "$PDFX/scripts/build_ebook_from_markdown.py" --title "DevOps Tricks" --subtitle "Complete Reference" \
    --stats "23 CHAPTERS · BEGINNER → ADVANCED" \
    --gen-cover "a small server scaling into a distributed cloud, racks/containers/nodes + glowing data-flow lines" \
    --page a4 --theme light --accent "#2563eb" --output handbook.pdf  ch01.md ch02.md ...

# or a pre-made cover / no cover (CSS gradient fallback)
$PY "$PDFX/scripts/build_ebook_from_markdown.py" --title "Notes" --input-dir ./docs --output notes.pdf
```
Each file's first `# H1` = chapter title. Options: `--gen-cover "<idea>"` (AI cover, 2:3/2K,
text-free, title overlaid in CSS), `--cover-image <file>`, `--page a4|6x9`, `--theme light|dark`,
`--accent "#hex"`, `--kicker`, `--stats`. Cover art calls Gemini (Nano Banana) **directly** via
the `google-genai` package — needs `GEMINI_API_KEY` (environment variable, `$PDFX/.env`,
the parent skills folder's `.env`, or the common `~/.agents/.env` / `~/.claude/.env` locations).
No other skill required; if the package or key is missing it degrades to a CSS gradient cover and
the build still succeeds. Recipes: `references/weasyprint-recipes.md`.

**Always visual-validate generation** (a PDF that compiles ≠ a PDF that looks good):
```bash
pdftoppm -png -r 150 -f 1 -l 1 handbook.pdf prev   # then Read prev-001.png and adjust
```

## B. Process existing PDFs
All via `scripts/pdf_process.py <subcommand>`:

| Command | Example |
|---------|---------|
| `info` | `$PY "$PDFX/scripts/pdf_process.py" info in.pdf [--password PW]` |
| `merge` | `$PY "$PDFX/scripts/pdf_process.py" merge out.pdf a.pdf b.pdf …` |
| `split` | `$PY "$PDFX/scripts/pdf_process.py" split in.pdf --ranges "1-3,4-6" --out-dir DIR` |
| `rotate` | `$PY "$PDFX/scripts/pdf_process.py" rotate in.pdf out.pdf --angle 90 [--pages 1,2]` |
| `watermark` | `$PY "$PDFX/scripts/pdf_process.py" watermark in.pdf out.pdf --text "DRAFT" [--opacity 0.12]` |
| `encrypt` / `decrypt` | `$PY "$PDFX/scripts/pdf_process.py" encrypt in.pdf out.pdf --password PW [--owner PW]` |
| `metadata` | `$PY "$PDFX/scripts/pdf_process.py" metadata in.pdf [--set Title=… --output out.pdf \| --in-place]` |
| `extract-text` | `$PY "$PDFX/scripts/pdf_process.py" extract-text in.pdf [--out t.txt] [--layout]` |
| `extract-tables` | `$PY "$PDFX/scripts/pdf_process.py" extract-tables in.pdf [--out t.csv]` |
| `ocr` (scanned) | `$PY "$PDFX/scripts/pdf_process.py" ocr scan.pdf --lang vie+eng [--out t.txt] [--dpi 300]` |
| `to-images` | `$PY "$PDFX/scripts/pdf_process.py" to-images in.pdf --out-dir DIR [--dpi 150]` |

**Forms** (separate scripts — run check first): `check_fillable_fields.py in.pdf` →
`fill_fillable_fields.py in.pdf fields.json out.pdf`. Non-fillable forms:
`fill_pdf_form_with_annotations.py`. Inspect fields: `extract_form_field_info.py`,
`check_bounding_boxes.py`. Guide: `references/forms.md`.

## Setup / install on any machine (self-contained — depends on NO other skill)
1. **Copy the whole `pdfx/` folder** to any target skills dir or project-local skill dir.
   Everything is bundled: scripts, references, examples, and `assets/fonts/`.
2. **Set `PDFX`** to the installed folder:
```bash
PDFX=/absolute/path/to/pdfx
PY=python
```
3. **Python deps** (into any venv; scripts run with that venv's python):
```bash
pip install weasyprint markdown pygments pypdf pdfplumber reportlab pytesseract pdf2image google-genai
```
4. **System tools**: `qpdf`, `poppler-utils` (pdftotext/pdftoppm/pdfinfo), `tesseract-ocr`
   (+ `tesseract-ocr-vie` for Vietnamese OCR), and WeasyPrint's Pango/cairo
   (Debian/Ubuntu: `libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0`; usually preinstalled).
5. **Optional** — AI covers: set `GEMINI_API_KEY` in env or a `.env` file beside the skill
   (`$PDFX/.env`). Without it, `--gen-cover` falls back to a gradient cover; everything else is unaffected.

No dependency on `ai-multimodal` or any other skill — `--gen-cover` calls `google-genai` directly.

## Files
- `scripts/build_ebook_from_markdown.py` — ebook/PDF generator (cover, TOC, code, bookmarks, `--gen-cover`).
- `scripts/pdf_process.py` — processing CLI (12 subcommands above).
- `scripts/{check_fillable_fields,fill_fillable_fields,fill_pdf_form_with_annotations,extract_form_field_info,check_bounding_boxes,convert_pdf_to_images,create_validation_image}.py` — form-filling toolkit.
- `references/` — `weasyprint-recipes.md` (design CSS), `pdf-manipulation-guide.md`, `forms.md` (form-filling guide), `ocr-extraction-patterns.md`, `reference.md`.
- `assets/fonts/` — bundled display fonts (Playfair Display, EB Garamond).
- `examples/` — sample chapters for a generation smoke test.

## Smoke test
```bash
$PY "$PDFX/scripts/build_ebook_from_markdown.py" --title "pdfx smoke" --input-dir "$PDFX/examples" --output /tmp/pdfx.pdf
$PY "$PDFX/scripts/pdf_process.py" info /tmp/pdfx.pdf
```
