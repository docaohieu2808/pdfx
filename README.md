# pdfx — complete PDF toolkit (Claude Code skill)

A self-contained [Claude Code](https://claude.ai/code) / agent **skill** that handles *any*
PDF task. Unlike typical `pdf` skills that only read or transform PDFs, **pdfx does both
directions** — it also *produces* publication-quality PDFs from Markdown.

> **One skill, two pillars.** Copy the `pdfx/` folder into any skills directory and it just
> works — bundled fonts, runnable CLI scripts, and reference guides. Depends on **no other skill**.

## A. Generate beautiful PDFs / ebooks (Markdown → PDF)
`Markdown → HTML (python-markdown + Pygments) → WeasyPrint → PDF` with published-grade print CSS:

- Designed cover — optional **AI art** generated inline via Gemini (free-tier key), or a
  pre-made image, or a CSS gradient fallback.
- Auto-numbered **Table of Contents** with dot leaders (real page numbers).
- **Syntax-highlighted** code blocks, clickable **PDF bookmarks**, `[B]/[I]/[A]/[!]` badges.
- Proper typography (bundled Playfair Display + EB Garamond), A4 or 6×9, light/dark themes.

```bash
PDFX=/path/to/pdfx ; PY=python
$PY "$PDFX/scripts/build_ebook_from_markdown.py" \
    --title "DevOps Tricks" --subtitle "Complete Reference" \
    --gen-cover "a server scaling into a distributed cloud, glowing data-flow lines" \
    --page a4 --theme light --accent "#2563eb" --output handbook.pdf  ch01.md ch02.md ...
```

## B. Process existing PDFs (extract / transform / fill)
One CLI, 12 subcommands — `scripts/pdf_process.py`:

| Area | Commands |
|------|----------|
| Inspect / convert | `info`, `to-images` |
| Extract | `extract-text` (+`--layout`), `extract-tables`, `ocr` (`--lang vie+eng`, scanned) |
| Transform | `merge`, `split`, `rotate`, `watermark`, `encrypt`, `decrypt`, `metadata` |
| Forms | `check_fillable_fields.py` → `fill_fillable_fields.py` (fillable) or `fill_pdf_form_with_annotations.py` (flat scans) |

```bash
$PY "$PDFX/scripts/pdf_process.py" ocr scan.pdf --lang vie+eng --out scan.txt
$PY "$PDFX/scripts/pdf_process.py" merge out.pdf a.pdf b.pdf
```

## Install
```bash
pip install weasyprint markdown pygments pypdf pdfplumber reportlab pytesseract pdf2image google-genai
# system: qpdf, poppler-utils, tesseract-ocr (+ tesseract-ocr-vie for Vietnamese), Pango/cairo
```
Optional AI covers: set `GEMINI_API_KEY` (env or a `.env` beside the skill). Without it,
`--gen-cover` falls back to a gradient cover and everything else is unaffected.

## Layout
```
pdfx/
├── SKILL.md          # full agent instructions (entry point)
├── scripts/          # build_ebook_from_markdown.py, pdf_process.py, form-filling toolkit
├── references/       # weasyprint-recipes, pdf-manipulation, forms, ocr-patterns, reference
├── assets/fonts/     # bundled display fonts (Playfair Display, EB Garamond) + OFL.txt
└── examples/         # sample chapters for a generation smoke test
```

## Smoke test
```bash
$PY "$PDFX/scripts/build_ebook_from_markdown.py" --title "pdfx smoke" --input-dir "$PDFX/examples" --output /tmp/pdfx.pdf
$PY "$PDFX/scripts/pdf_process.py" info /tmp/pdfx.pdf
```

---
**Author:** hieudc · **License:** MIT (skill code). Bundled fonts are under SIL OFL-1.1 — see
[`assets/fonts/OFL.txt`](assets/fonts/OFL.txt).
