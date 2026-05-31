#!/usr/bin/env bash
# pdfx installer — grabs everything the skill can use, in one shot.
# Safe to re-run.  Usage: ./install.sh [--lean]
#   default : full toolkit (incl. camelot ~250MB and Mermaid CLI + Chromium ~1.7GB)
#   --lean  : skip Chromium/Mermaid + camelot (both auto-install on first use anyway)
# System packages are best-effort (need a package manager + sudo); Python packages go
# into the chosen venv. Override the interpreter with PDFX_PY=/path/to/venv/bin/python.
set -uo pipefail

LEAN=0; [ "${1:-}" = "--lean" ] && LEAN=1

# ---- pick a Python interpreter / venv -------------------------------------------------
PY="${PDFX_PY:-}"
if [ -z "$PY" ]; then
  for c in "$HOME/.claude/skills/.venv/bin/python3" "$HOME/.agents/skills/.venv/bin/python3" python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
echo "▶ Python: $PY"
[ "$LEAN" = 1 ] && echo "  (lean: skipping Chromium/Mermaid + camelot — auto-installed on first use)"

# ---- Python dependencies --------------------------------------------------------------
echo "▶ Installing core Python packages…"
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q \
  weasyprint markdown pygments \
  pypdf pikepdf pymupdf pymupdf4llm pdfplumber reportlab img2pdf \
  pytesseract pdf2image ocrmypdf google-genai \
  && echo "  ✓ core Python packages OK" || echo "  ⚠ some core packages failed (see above)"
if [ "$LEAN" = 0 ]; then
  echo "▶ camelot (borderless tables; pulls opencv/pandas ~250MB)…"
  "$PY" -m pip install -q camelot-py && echo "  ✓ camelot OK" || echo "  ⚠ camelot failed"
fi

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
if [ "$LEAN" = 1 ]; then
  echo "▶ Mermaid CLI: skipped (lean). ```mermaid``` blocks use npx on first use"
  echo "  (downloads Chromium ~1.7GB then). Inline <svg> needs nothing."
elif command -v npm >/dev/null 2>&1; then
  echo "▶ Mermaid CLI (npm -g; pulls Chromium ~1.7GB)…"; npm install -g @mermaid-js/mermaid-cli >/dev/null 2>&1 \
    && echo "  ✓ mmdc OK" || echo "  ⚠ mmdc install failed (mermaid still works via npx on first use)"
else
  echo "  ⓘ no npm — mermaid diagrams use npx on first use (auto-downloads), or skip"
fi

# ---- veraPDF (PDF/A validator) --------------------------------------------------------
VERAPDF_HOME="$HOME/.local/share/verapdf"
if [ -x "$VERAPDF_HOME/verapdf" ]; then
  echo "▶ veraPDF already installed ($VERAPDF_HOME)"
else
  if ! command -v java >/dev/null 2>&1; then
    echo "▶ Installing Java (veraPDF needs a JRE)…"
    if   command -v apt-get >/dev/null 2>&1; then $SUDO apt-get install -y -qq default-jre-headless || true
    elif command -v brew    >/dev/null 2>&1; then brew install openjdk || true
    elif command -v dnf     >/dev/null 2>&1; then $SUDO dnf install -y -q java-latest-openjdk-headless || true
    fi
  fi
  if command -v java >/dev/null 2>&1 && command -v unzip >/dev/null 2>&1; then
    echo "▶ Installing veraPDF → $VERAPDF_HOME …"
    TMP=$(mktemp -d)
    if curl -fsSL -o "$TMP/v.zip" https://software.verapdf.org/releases/verapdf-installer.zip \
       && unzip -q "$TMP/v.zip" -d "$TMP"; then
      DIR=$(ls -d "$TMP"/verapdf-greenfield-*/ | head -1)
      cat > "$TMP/auto.xml" <<XML
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<AutomatedInstallation langpack="eng">
    <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel id="welcome"/>
    <com.izforge.izpack.panels.target.TargetPanel id="install_dir"><installpath>$VERAPDF_HOME</installpath></com.izforge.izpack.panels.target.TargetPanel>
    <com.izforge.izpack.panels.packs.PacksPanel id="sdk_pack_select">
        <pack index="0" name="veraPDF GUI" selected="true"/>
        <pack index="1" name="veraPDF Validation model" selected="true"/>
        <pack index="2" name="veraPDF Documentation" selected="false"/>
        <pack index="3" name="veraPDF Sample Plugins" selected="false"/>
        <pack index="4" name="veraPDF Mac and *nix Startup Scripts" selected="true"/>
    </com.izforge.izpack.panels.packs.PacksPanel>
    <com.izforge.izpack.panels.install.InstallPanel id="install"/>
    <com.izforge.izpack.panels.finish.SimpleFinishPanel id="finish"/>
</AutomatedInstallation>
XML
      bash "${DIR}verapdf-install" "$TMP/auto.xml" >/dev/null 2>&1 \
        && echo "  ✓ veraPDF OK ($("$VERAPDF_HOME/verapdf" --version 2>/dev/null | head -1))" \
        || echo "  ⚠ veraPDF install failed"
    else
      echo "  ⚠ veraPDF download/unzip failed"
    fi
    rm -rf "$TMP"
  else
    echo "  ⚠ veraPDF needs java + unzip — skipped (PDF/A generation still works; only --validate needs it)"
  fi
fi

# ---- capability report ----------------------------------------------------------------
echo ""; echo "▶ Capability check:"
if [ -x "$VERAPDF_HOME/verapdf" ] || command -v verapdf >/dev/null 2>&1; then VP="✓"; else VP="— (PDF/A validation)"; fi
printf "  %-12s %s\n" "verapdf" "$VP"
for t in pdfinfo pdftoppm pdfimages pdffonts pdftohtml pdfdetach qpdf gs mutool img2pdf tesseract mmdc java; do
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
echo ""
echo "✅ pdfx install done. GEMINI_API_KEY (for AI cover + Gemini OCR) goes in ~/.claude/.env"
echo "   Disk: skill code ~3MB · veraPDF ~33MB · Python deps ~250MB."
[ "$LEAN" = 0 ] && echo "   + Mermaid Chromium ~1.7GB (full mode). Use --lean to skip it (mermaid then on-demand via npx)."
