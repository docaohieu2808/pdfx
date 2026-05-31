"""Overlay & info ops: watermark (diagonal), stamp (header/footer/page numbers),
metadata (get/set)."""
import io, os, pathlib, tempfile
from . import _util


def cmd_watermark(a):
    pypdf = _util.need("pypdf"); _util.need("reportlab")
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color
    r = pypdf.PdfReader(a.input)
    stamps = {}

    def stamp_for(W, H):
        buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H))
        c.setFont("Helvetica-Bold", a.size)
        c.setFillColor(Color(0.5, 0.5, 0.5, alpha=a.opacity))
        c.saveState(); c.translate(W / 2, H / 2); c.rotate(45)
        c.drawCentredString(0, 0, a.text); c.restoreState(); c.save(); buf.seek(0)
        return pypdf.PdfReader(buf).pages[0]

    w = pypdf.PdfWriter()
    for pg in r.pages:
        box = pg.mediabox; key = (round(float(box.width), 1), round(float(box.height), 1))
        stamps.setdefault(key, stamp_for(*key))
        pg.merge_page(stamps[key]); w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"watermarked '{a.text}' -> {a.output}")


def cmd_stamp(a):
    """Add running header/footer text. Tokens {page} {pages} expand per page.
    --pos one of: header-left/center/right, footer-left/center/right."""
    fitz = _util.need("fitz")
    doc = fitz.open(a.input)
    total = doc.page_count
    vert, horiz = (a.pos.split("-") + ["center"])[:2]
    for i, page in enumerate(doc, 1):
        text = a.text.replace("{page}", str(i)).replace("{pages}", str(total))
        rc = page.rect
        y = 28 if vert == "header" else rc.height - 22
        tw = fitz.get_text_length(text, fontsize=a.size)
        x = {"left": 40, "center": (rc.width - tw) / 2, "right": rc.width - tw - 40}[horiz]
        page.insert_text((x, y), text, fontsize=a.size, color=(0.3, 0.3, 0.3))
    doc.save(a.output)
    print(f"stamped {a.pos} -> {a.output}")


def cmd_metadata(a):
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    if not a.set:
        for k, v in (r.metadata or {}).items():
            print(f"{k}: {v}")
        return
    if not a.output and not a.in_place:
        _util.sys.exit("metadata --set requires --output OUT.pdf or --in-place")
    w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.add_metadata({f"/{k}": v for k, v in (kv.split("=", 1) for kv in a.set)})
    out = pathlib.Path(a.output or a.input)
    if a.in_place:
        tmp = tempfile.NamedTemporaryFile(prefix=f"{out.name}.", suffix=".tmp",
                                          dir=str(out.parent or pathlib.Path(".")), delete=False)
        tmp_path = pathlib.Path(tmp.name)
        try:
            with tmp:
                w.write(tmp)
            os.replace(tmp_path, out)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    else:
        with open(out, "wb") as fh:
            w.write(fh)
    print(f"metadata set -> {out}")


def register(sub):
    sp = sub.add_parser("watermark", help="diagonal watermark on every page"); sp.set_defaults(fn=cmd_watermark)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--text", required=True)
    sp.add_argument("--opacity", type=float, default=0.12); sp.add_argument("--size", type=int, default=72)
    sp = sub.add_parser("stamp", help="header/footer/page-number text"); sp.set_defaults(fn=cmd_stamp)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--text", required=True)
    sp.add_argument("--pos", default="footer-center"); sp.add_argument("--size", type=int, default=9)
    sp = sub.add_parser("metadata", help="get or --set Title=… Author=…"); sp.set_defaults(fn=cmd_metadata)
    sp.add_argument("input"); sp.add_argument("--set", nargs="*"); sp.add_argument("--output")
    sp.add_argument("--in-place", action="store_true")
