"""OCR ops with two engines:
  • tesseract  — offline, great for English/Latin; for Vietnamese pass --lang vie
                 (default --lang eng MANGLES diacritics). Weak on noisy real scans.
  • gemini     — vision LLM (gemini-2.5-flash); far more reliable for Vietnamese and
                 messy scans, preserves diacritics. Needs GEMINI_API_KEY + network.

`ocr` extracts text; `--engine auto` (default) uses Gemini for Vietnamese when a key is
present, else tesseract. `ocr-searchable` (text layer) is tesseract-only — an LLM can't
position glyphs — so pass --lang vie for Vietnamese.
"""
import io, sys, pathlib
from . import _util


def _resolve_engine(engine, lang, have_key):
    if engine == "tesseract":
        return "tesseract"
    if engine == "gemini":
        if not have_key:
            sys.exit("--engine gemini needs GEMINI_API_KEY (env or ~/.claude/.env).")
        return "gemini"
    # auto: prefer Gemini for Vietnamese (tesseract drops VN diacritics on real scans)
    if have_key and "vie" in lang:
        return "gemini"
    return "tesseract"


def _gemini_ocr(images, model):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from pdfx_lib.cover import gemini_key
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=gemini_key())
    prompt = ("Transcribe ALL text in this image exactly as written. Preserve Vietnamese "
              "diacritics and every accent. Keep line breaks. Output ONLY the transcribed "
              "text — no commentary, no markdown fences.")
    out = []
    for im in images:
        buf = io.BytesIO(); im.save(buf, format="PNG")
        r = client.models.generate_content(
            model=model, contents=[types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"), prompt])
        out.append((r.text or "").strip())
    return "\n\n".join(out)


def cmd_ocr(a):
    _util.need("pdf2image")
    from pdf2image import convert_from_path
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from pdfx_lib.cover import gemini_key
    engine = _resolve_engine(a.engine, a.lang, bool(gemini_key()))
    pages = convert_from_path(a.input, dpi=a.dpi)
    if engine == "gemini":
        print(f"[ocr] engine=gemini ({a.model})", file=sys.stderr)
        txt = _gemini_ocr(pages, a.model)
    else:
        _util.need("pytesseract"); _util.need_tool("tesseract", "tesseract-ocr")
        import pytesseract
        if "vie" not in a.lang:
            print("[ocr] engine=tesseract, lang=eng — for Vietnamese use --lang vie "
                  "or --engine gemini (diacritics).", file=sys.stderr)
        txt = "\n\n".join(pytesseract.image_to_string(im, lang=a.lang) for im in pages)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print(f"ocr ({engine}/{a.lang}) -> {a.out} ({len(txt)} chars)")
    else:
        print(txt)


def cmd_ocr_searchable(a):
    """Add an invisible OCR text layer (selectable/searchable). Tesseract only."""
    _util.need("pytesseract"); _util.need("pdf2image"); _util.need("pypdf")
    _util.need_tool("tesseract", "tesseract-ocr")
    import pytesseract
    from pdf2image import convert_from_path
    import pypdf
    if "vie" not in a.lang:
        print("[ocr-searchable] lang=eng — for Vietnamese pass --lang vie.", file=sys.stderr)
    pages = convert_from_path(a.input, dpi=a.dpi)
    writer = pypdf.PdfWriter()
    for im in pages:
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(im, lang=a.lang, extension="pdf")
        for pg in pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages:
            writer.add_page(pg)
    with open(a.output, "wb") as fh:
        writer.write(fh)
    print(f"searchable PDF ({a.lang}) -> {a.output} ({len(pages)} pages)")


def register(sub):
    sp = sub.add_parser("ocr", help="extract text from a scanned PDF (tesseract/gemini)")
    sp.set_defaults(fn=cmd_ocr)
    sp.add_argument("input"); sp.add_argument("--out"); sp.add_argument("--lang", default="eng")
    sp.add_argument("--dpi", type=int, default=300)
    sp.add_argument("--engine", default="auto", choices=["auto", "tesseract", "gemini"])
    sp.add_argument("--model", default="gemini-2.5-flash", help="Gemini vision model")
    sp = sub.add_parser("ocr-searchable", help="add a searchable text layer (tesseract)")
    sp.set_defaults(fn=cmd_ocr_searchable)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--lang", default="eng")
    sp.add_argument("--dpi", type=int, default=300)
