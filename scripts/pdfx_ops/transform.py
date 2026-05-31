"""Page-level structural ops: merge, split, rotate, pages (remove/keep/reorder),
nup (N pages per sheet), crop."""
import pathlib
from . import _util


def cmd_merge(a):
    pypdf = _util.need("pypdf")
    w = pypdf.PdfWriter()
    for f in a.inputs:
        for pg in pypdf.PdfReader(f).pages:
            w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"merged {len(a.inputs)} file(s) -> {a.output}")


def cmd_split(a):
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    n = len(r.pages)
    outdir = _util.out_dir(a.out_dir)
    stem = pathlib.Path(a.input).stem
    groups = _util.parse_groups(a.ranges, n) if a.ranges else [[i] for i in range(1, n + 1)]
    for idx, grp in enumerate(groups, 1):
        w = pypdf.PdfWriter()
        for p in grp:
            w.add_page(r.pages[p - 1])
        out = outdir / f"{stem}_part{idx:02d}.pdf"
        with open(out, "wb") as fh:
            w.write(fh)
        print(f"  -> {out}")


def cmd_rotate(a):
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    w = pypdf.PdfWriter()
    pages = set(_util.parse_pages(a.pages, len(r.pages))) if a.pages else None
    for i, pg in enumerate(r.pages, 1):
        if pages is None or i in pages:
            pg.rotate(a.angle)
        w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"rotated {a.angle}° -> {a.output}")


def cmd_pages(a):
    """Remove, keep, or reorder pages. --keep takes precedence (also reorders)."""
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    n = len(r.pages)
    if a.keep:
        order = _util.parse_pages(a.keep, n)
    elif a.remove:
        drop = set(_util.parse_pages(a.remove, n))
        order = [i for i in range(1, n + 1) if i not in drop]
    else:
        _util.sys.exit("pages requires --keep '3,1,2' or --remove '4,5'")
    w = pypdf.PdfWriter()
    for p in order:
        w.add_page(r.pages[p - 1])
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"pages {'keep' if a.keep else 'remove'} -> {a.output} ({len(order)} pages)")


def cmd_nup(a):
    """Place N source pages onto each output sheet (2 or 4 up)."""
    fitz = _util.need("fitz")
    if a.n not in (2, 4):
        _util.sys.exit("--n must be 2 or 4")
    src = fitz.open(a.input)
    out = fitz.open()
    cols, rows = (2, 1) if a.n == 2 else (2, 2)
    # output sheet = landscape A4 for 2-up, portrait A4 for 4-up
    W, H = (842, 595) if a.n == 2 else (595, 842)
    for start in range(0, src.page_count, a.n):
        sheet = out.new_page(width=W, height=H)
        cw, ch = W / cols, H / rows
        for slot in range(a.n):
            idx = start + slot
            if idx >= src.page_count:
                break
            c, rr = slot % cols, slot // cols
            rect = fitz.Rect(c * cw, rr * ch, (c + 1) * cw, (rr + 1) * ch)
            sheet.show_pdf_page(rect, src, idx)
    out.save(a.output)
    print(f"{a.n}-up -> {a.output} ({out.page_count} sheets)")


def cmd_crop(a):
    """Crop every page by margin percentages: --margins 't,r,b,l' (percent of page)."""
    fitz = _util.need("fitz")
    try:
        t, rgt, b, l = (float(x) for x in a.margins.split(","))
    except ValueError:
        _util.sys.exit("--margins must be 't,r,b,l' e.g. '5,5,5,5' (percent)")
    doc = fitz.open(a.input)
    for page in doc:
        rc = page.rect
        page.set_cropbox(fitz.Rect(
            rc.x0 + rc.width * l / 100, rc.y0 + rc.height * t / 100,
            rc.x1 - rc.width * rgt / 100, rc.y1 - rc.height * b / 100))
    doc.save(a.output)
    print(f"cropped {a.margins}% -> {a.output}")


def register(sub):
    sp = sub.add_parser("merge", help="concatenate PDFs"); sp.set_defaults(fn=cmd_merge)
    sp.add_argument("output"); sp.add_argument("inputs", nargs="+")
    sp = sub.add_parser("split", help="split into per-page or per-range files"); sp.set_defaults(fn=cmd_split)
    sp.add_argument("input"); sp.add_argument("--ranges"); sp.add_argument("--out-dir")
    sp = sub.add_parser("rotate", help="rotate pages by angle"); sp.set_defaults(fn=cmd_rotate)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--angle", type=int, default=90); sp.add_argument("--pages")
    sp = sub.add_parser("pages", help="remove / keep / reorder pages"); sp.set_defaults(fn=cmd_pages)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--keep"); sp.add_argument("--remove")
    sp = sub.add_parser("nup", help="N pages per sheet (2 or 4 up)"); sp.set_defaults(fn=cmd_nup)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--n", type=int, default=2)
    sp = sub.add_parser("crop", help="crop page margins (percent)"); sp.set_defaults(fn=cmd_crop)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--margins", required=True)
