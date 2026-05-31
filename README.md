# pdfx — complete PDF toolkit (Claude Code skill)

A self-contained [Claude Code](https://claude.ai/code) / agent **skill** for *anything* PDF.
Unlike typical `pdf` skills that only read or transform PDFs, **pdfx does both directions** —
it also *produces* publication-quality PDFs from Markdown.

> **One skill, two pillars.** Copy the `pdfx/` folder into any skills directory and it just
> works — bundled fonts, modular CLI scripts, reference guides. Depends on **no other skill**.
> Optional heavy engines auto-install on first use (or run `install.sh`).

## A. Generate beautiful PDFs / ebooks (Markdown → PDF)
`Markdown → HTML (python-markdown + Pygments) → WeasyPrint → PDF` with published-grade print CSS:

- Designed cover — optional **AI art** via Gemini (free-tier key), a pre-made image, or a gradient.
- Auto-numbered **TOC** with dot leaders + real page numbers; optional **depth-2** sub-entries.
- **Part dividers** (`--parts`), a back-of-book **A-Z index** (`--index`), clickable **PDF bookmarks**.
- **Diagrams that actually render:** inline `<svg>` (shielded from `md_in_html`) **and** ` ```mermaid ` fences auto-rendered to SVG (Vietnamese-safe labels).
- Syntax-highlighted code, `[B]/[I]/[A]/[!]` badges, bundled Playfair Display + EB Garamond, A4/6×9, light/dark, `--preview` to auto-render page PNGs.

```bash
PDFX=/path/to/pdfx ; PY=python
$PY "$PDFX/scripts/build_ebook_from_markdown.py" \
    --title "DevOps Handbook" --subtitle "Complete Reference" \
    --gen-cover "a server scaling into a distributed cloud, glowing data-flow lines" \
    --parts "1=Foundations,7=Build & Ship" --toc-depth 2 --index --preview \
    --page a4 --theme light --accent "#2563eb" --output handbook.pdf  ch01.md ch02.md ...
```

## B. Process existing PDFs — `scripts/pdf_process.py` (35 subcommands)

| Group | Commands |
|-------|----------|
| **Transform** | `merge` · `split` · `rotate` · `pages` (remove/keep/reorder) · `nup` · `crop` |
| **Extract** | `extract-text` · `extract-tables` (+`--engine camelot` for borderless) · `extract-images` · `to-images` · `to-html` · `to-markdown` · `fonts` · `links` · `attachments` · `bookmarks` |
| **Security** | `encrypt` · `decrypt` · `unlock` · `redact` (true removal, `--ignore-case`/`--regex`) · `permissions` |
| **Optimize** | `compress` · `linearize` · `pdfa` (veraPDF-valid PDF/A-2b, `--validate`) · `repair` |
| **Annotate** | `watermark` · `stamp` (headers/footers/page numbers) · `metadata` |
| **Convert-in** | `from-images` · `from-html` · `from-url` |
| **Analyze** | `info` · `compare` (visual or text diff) · `validate` (PDF/A via veraPDF) |
| **OCR** | `ocr` (tesseract or **Gemini**, auto for Vietnamese) · `ocr-searchable` (ocrmypdf text layer) |
| **Forms** | `check_fillable_fields.py` → `fill_fillable_fields.py` (fillable) or `fill_pdf_form_with_annotations.py` (flat scans — stamps a Unicode font, **Vietnamese-safe**) |

```bash
$PY "$PDFX/scripts/pdf_process.py" compress big.pdf small.pdf --quality ebook
$PY "$PDFX/scripts/pdf_process.py" ocr scan.pdf --lang vie --out scan.txt        # Gemini auto for vi
$PY "$PDFX/scripts/pdf_process.py" pdfa report.pdf archive.pdf --validate         # PDF/A + veraPDF check
$PY "$PDFX/scripts/pdf_process.py" extract-tables in.pdf --engine camelot --flavor stream
```

🇻🇳 **Vietnamese-aware:** Gemini OCR (auto for `--lang vie`) and Unicode-font form stamping preserve
diacritics where plain tesseract / base-font annotations drop them.

## Install
```bash
bash install.sh            # full toolkit (incl. Mermaid+Chromium ~1.7GB, camelot ~250MB)
bash install.sh --lean     # skip the heavy optional engines (auto-install on first use)
```
`install.sh` installs Python packages into the chosen venv (set `PDFX_PY=…`), system tools via
apt/brew/dnf (poppler, qpdf, ghostscript, mupdf-tools, tesseract + Vietnamese, img2pdf, pango/cairo),
the Mermaid CLI, and **veraPDF** (PDF/A validator), then prints a capability report.

**Or piecemeal:**
```bash
pip install weasyprint markdown pygments pypdf pikepdf pymupdf pymupdf4llm pdfplumber \
    reportlab img2pdf pytesseract pdf2image ocrmypdf camelot-py google-genai
# system: qpdf, ghostscript, poppler-utils, mupdf-tools, tesseract-ocr (+ -vie), img2pdf, Pango/cairo
```
Commands that need an optional package (`pymupdf4llm`, `ocrmypdf`, `camelot-py`) **pip-install it on
first use** (`PDFX_NO_AUTOINSTALL=1` to disable). Set `GEMINI_API_KEY` (env or `~/.claude/.env`) for
AI covers + Gemini OCR; without it, `--gen-cover` uses a gradient and OCR uses tesseract.

**Disk:** skill code ~3 MB · veraPDF ~33 MB · Python deps ~250 MB · Mermaid Chromium ~1.7 GB (full
only). Lean install ≈ 290 MB; the skill itself is tiny — the weight is optional engines.

## Layout
```
pdfx/
├── SKILL.md          # full agent instructions (entry point)
├── install.sh        # one-shot dependency installer (--lean for a minimal set)
├── scripts/
│   ├── build_ebook_from_markdown.py   # generator (orchestrates pdfx_lib/)
│   ├── pdf_process.py                 # thin dispatcher over pdfx_ops/
│   ├── pdfx_lib/     # cover · mermaid · markdown_render · toc_index · styles
│   ├── pdfx_ops/     # transform · extract · security · optimize · annotate · convert · analyze · ocr
│   └── *form*.py     # form-filling toolkit
├── references/       # weasyprint-recipes · pdf-manipulation · forms · ocr-patterns · gemini-ocr-model · reference
├── assets/fonts/     # bundled display fonts (Playfair Display, EB Garamond) + OFL.txt
└── examples/         # sample chapters (inline SVG + mermaid + glossary) for a smoke test
```

## Smoke test
```bash
$PY "$PDFX/scripts/build_ebook_from_markdown.py" --title "pdfx smoke" --input-dir "$PDFX/examples" --output /tmp/pdfx.pdf --preview
$PY "$PDFX/scripts/pdf_process.py" info /tmp/pdfx.pdf
$PY "$PDFX/scripts/pdf_process.py" pdfa /tmp/pdfx.pdf /tmp/pdfx-a.pdf --validate
```

---
**Author:** hieudc · **License:** MIT (skill code). Bundled fonts are under SIL OFL-1.1 — see
[`assets/fonts/OFL.txt`](assets/fonts/OFL.txt).
