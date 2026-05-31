"""Pull content out of a PDF: text, tables, embedded images, page rasters,
HTML/Markdown, fonts, links, attachments, bookmarks (outline)."""
import csv, pathlib, subprocess
from . import _util


def cmd_extract_text(a):
    import shutil
    if a.layout and shutil.which("pdftotext"):
        txt = subprocess.run(["pdftotext", "-layout", a.input, "-"], capture_output=True, text=True).stdout
    else:
        pypdf = _util.need("pypdf")
        txt = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(a.input).pages)
    _emit(txt, a.out, "text")


def cmd_extract_tables(a):
    """pdfplumber (default; ruled tables) or camelot (--engine camelot --flavor stream
    handles borderless tables)."""
    rows = []
    if a.engine == "camelot":
        camelot = _util.ensure("camelot", "camelot-py")
        for t in camelot.read_pdf(a.input, flavor=a.flavor, pages=a.pages or "all"):
            rows += t.df.values.tolist() + [[]]
    else:
        pdfplumber = _util.need("pdfplumber")
        with pdfplumber.open(a.input) as pdf:
            for page in pdf.pages:
                for t in page.extract_tables():
                    rows += t + [[]]
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        print(f"tables -> {a.out} ({len(rows)} rows)")
    else:
        for r in rows:
            print("\t".join(str(c or "") for c in r))


def cmd_extract_images(a):
    _util.need_tool("pdfimages", "poppler-utils")
    outdir = _util.out_dir(a.out_dir)
    prefix = str(outdir / pathlib.Path(a.input).stem)
    _util.run(["pdfimages", "-all", a.input, prefix])
    n = len(list(outdir.glob(f"{pathlib.Path(a.input).stem}*")))
    print(f"extracted {n} embedded image(s) -> {outdir}/")


def cmd_to_images(a):
    _util.need_tool("pdftoppm", "poppler-utils")
    outdir = _util.out_dir(a.out_dir)
    prefix = str(outdir / pathlib.Path(a.input).stem)
    _util.run(["pdftoppm", f"-{a.fmt}", "-r", str(a.dpi), a.input, prefix])
    print(f"page rasters -> {outdir}/ (dpi {a.dpi}, {a.fmt})")


def cmd_to_html(a):
    _util.need_tool("pdftohtml", "poppler-utils")
    out = a.out or str(pathlib.Path(a.input).with_suffix(".html"))
    _util.run(["pdftohtml", "-s", "-noframes", "-q", a.input, out])
    print(f"html -> {out}")


def cmd_to_markdown(a):
    """Markdown via pymupdf4llm if present (best structure), else layout text."""
    out = a.out or str(pathlib.Path(a.input).with_suffix(".md"))
    try:
        pymupdf4llm = _util.ensure("pymupdf4llm")
        md = pymupdf4llm.to_markdown(a.input)
    except SystemExit:  # auto-install unavailable (offline) — basic fitz text fallback
        fitz = _util.need("fitz")
        doc = fitz.open(a.input)
        md = "\n\n---\n\n".join(page.get_text("text") for page in doc)
    pathlib.Path(out).write_text(md, encoding="utf-8")
    print(f"markdown -> {out} ({len(md)} chars)")


def cmd_fonts(a):
    _util.need_tool("pdffonts", "poppler-utils")
    subprocess.run(["pdffonts", a.input])


def cmd_links(a):
    fitz = _util.need("fitz")
    doc = fitz.open(a.input)
    count = 0
    for i, page in enumerate(doc, 1):
        for lk in page.get_links():
            uri = lk.get("uri") or (f"page {lk['page']+1}" if lk.get("page", -1) >= 0 else "?")
            print(f"p{i}: {uri}")
            count += 1
    print(f"-- {count} link(s)")


def cmd_attachments(a):
    _util.need_tool("pdfdetach", "poppler-utils")
    if a.save:
        outdir = _util.out_dir(a.out_dir)
        _util.run(["pdfdetach", "-saveall", "-o", str(outdir), a.input])
        print(f"attachments saved -> {outdir}/")
    else:
        subprocess.run(["pdfdetach", "-list", a.input])


def cmd_bookmarks(a):
    fitz = _util.need("fitz")
    toc = fitz.open(a.input).get_toc()
    if not toc:
        print("(no bookmarks/outline)")
        return
    for level, title, page in toc:
        print(f"{'  ' * (level - 1)}- {title}  (p{page})")


def _emit(txt, out, label):
    if out:
        pathlib.Path(out).write_text(txt, encoding="utf-8")
        print(f"{label} -> {out} ({len(txt)} chars)")
    else:
        print(txt)


def register(sub):
    sp = sub.add_parser("extract-text", help="extract text (—layout keeps columns)"); sp.set_defaults(fn=cmd_extract_text)
    sp.add_argument("input"); sp.add_argument("--out"); sp.add_argument("--layout", action="store_true")
    sp = sub.add_parser("extract-tables", help="extract tables to CSV (pdfplumber/camelot)"); sp.set_defaults(fn=cmd_extract_tables)
    sp.add_argument("input"); sp.add_argument("--out")
    sp.add_argument("--engine", default="pdfplumber", choices=["pdfplumber", "camelot"])
    sp.add_argument("--flavor", default="stream", choices=["stream", "lattice"], help="camelot: stream=borderless, lattice=ruled")
    sp.add_argument("--pages", help="camelot page range, e.g. '1,2' or '1-3' (default all)")
    sp = sub.add_parser("extract-images", help="extract embedded raster images"); sp.set_defaults(fn=cmd_extract_images)
    sp.add_argument("input"); sp.add_argument("--out-dir")
    sp = sub.add_parser("to-images", help="render pages to PNG/JPEG"); sp.set_defaults(fn=cmd_to_images)
    sp.add_argument("input"); sp.add_argument("--out-dir"); sp.add_argument("--dpi", type=int, default=150); sp.add_argument("--fmt", default="png", choices=["png", "jpeg"])
    sp = sub.add_parser("to-html", help="convert to HTML"); sp.set_defaults(fn=cmd_to_html)
    sp.add_argument("input"); sp.add_argument("--out")
    sp = sub.add_parser("to-markdown", help="convert to Markdown"); sp.set_defaults(fn=cmd_to_markdown)
    sp.add_argument("input"); sp.add_argument("--out")
    sp = sub.add_parser("fonts", help="list embedded fonts"); sp.set_defaults(fn=cmd_fonts); sp.add_argument("input")
    sp = sub.add_parser("links", help="list hyperlinks"); sp.set_defaults(fn=cmd_links); sp.add_argument("input")
    sp = sub.add_parser("attachments", help="list/save embedded files"); sp.set_defaults(fn=cmd_attachments)
    sp.add_argument("input"); sp.add_argument("--save", action="store_true"); sp.add_argument("--out-dir")
    sp = sub.add_parser("bookmarks", help="print outline/bookmarks"); sp.set_defaults(fn=cmd_bookmarks); sp.add_argument("input")
