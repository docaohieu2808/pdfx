#!/usr/bin/env bash
# pdfx installer — grabs everything the skill can use, in one shot.
# Safe to re-run. System packages are best-effort (need a package manager + sudo);
# Python packages always install into the chosen venv. Override the interpreter with
#   PDFX_PY=/path/to/venv/bin/python ./install.sh
set -uo pipefail

# ---- pick a Python interpreter / venv -------------------------------------------------
PY="${PDFX_PY:-}"
if [ -z "$PY" ]; then
  for c in "$HOME/.claude/skills/.venv/bin/python3" "$HOME/.agents/skills/.venv/bin/python3" python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
echo "▶ Python: $PY"

# ---- Python dependencies (always) -----------------------------------------------------
echo "▶ Installing Python packages…"
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q \
  weasyprint markdown pygments \
  pypdf pikepdf pymupdf pymupdf4llm pdfplumber reportlab img2pdf \
  pytesseract pdf2image ocrmypdf camelot-py \
  google-genai \
  && echo "  ✓ Python packages OK" || echo "  ⚠ some Python packages failed (see above)"

# ---- system tools (best-effort) -------------------------------------------------------
SUDO=""; [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"
APT="poppler-utils qpdf ghostscript mupdf-tools tesseract-ocr tesseract-ocr-vie img2pdf \
     pngquant unpaper libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 fonts-liberation"
BREW="poppler qpdf ghostscript mupdf-tools tesseract tesseract-lang img2pdf pngquant unpaper pango cairo gdk-pixbuf"
DNF="poppler-utils qpdf ghostscript mupdf tesseract tesseract-langpack-vie img2pdf pngquant unpaper pango cairo gdk-pixbuf2"
if command -v apt-get >/dev/null 2>&1; then
  echo "▶ apt-get system tools…"; $SUDO apt-get update -qq && $SUDO apt-get install -y -qq $APT && echo "  ✓ system tools OK" || echo "  ⚠ apt step needs sudo / failed"
elif command -v brew >/dev/null 2>&1; then
  echo "▶ brew system tools…"; brew install $BREW && echo "  ✓ system tools OK" || echo "  ⚠ brew step failed"
elif command -v dnf >/dev/null 2>&1; then
  echo "▶ dnf system tools…"; $SUDO dnf install -y -q $DNF && echo "  ✓ system tools OK" || echo "  ⚠ dnf step needs sudo / failed"
else
  echo "  ⚠ no apt/brew/dnf — install poppler, qpdf, ghostscript, mupdf-tools, tesseract(+vie), img2pdf manually"
fi

# ---- Mermaid CLI (optional, for ```mermaid diagrams) ----------------------------------
if command -v npm >/dev/null 2>&1; then
  echo "▶ Mermaid CLI (npm -g)…"; npm install -g @mermaid-js/mermaid-cli >/dev/null 2>&1 \
    && echo "  ✓ mmdc OK" || echo "  ⚠ mmdc install failed (mermaid still works via npx on first use)"
else
  echo "  ⓘ no npm — mermaid diagrams use npx on first use (auto-downloads), or skip"
fi

# ---- capability report ----------------------------------------------------------------
echo ""; echo "▶ Capability check:"
for t in pdfinfo pdftoppm pdfimages pdffonts pdftohtml pdfdetach qpdf gs mutool img2pdf tesseract ocrmypdf mmdc; do
  printf "  %-12s %s\n" "$t" "$(command -v "$t" >/dev/null 2>&1 && echo ✓ || echo '— (optional/missing)')"
done
"$PY" - <<'PYEOF'
mods=["weasyprint","markdown","pypdf","pikepdf","fitz","pdfplumber","reportlab","img2pdf",
      "pytesseract","pdf2image","pymupdf4llm","ocrmypdf","camelot","google.genai"]
import importlib
for m in mods:
    try: importlib.import_module(m); print(f"  {m:14} ✓")
    except Exception: print(f"  {m:14} — (missing)")
PYEOF
echo ""; echo "✅ pdfx install done. GEMINI_API_KEY (for AI cover + Gemini OCR) goes in ~/.claude/.env"
