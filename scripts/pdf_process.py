#!/usr/bin/env python3
"""pdfx processing CLI — transform & extract existing PDFs.

Subcommands: info, merge, split, rotate, watermark, encrypt, decrypt, metadata,
extract-text, extract-tables, ocr, to-images.

Run with the skills venv, e.g.:
  python pdf_process.py merge out.pdf a.pdf b.pdf
  python pdf_process.py ocr scan.pdf --lang vie+eng --out scan.txt

For form-filling use the dedicated scripts (check_fillable_fields.py, fill_fillable_fields.py).
For generating beautiful ebooks/reports use build_ebook_from_markdown.py.
"""
import argparse, os, sys, subprocess, shutil, pathlib, tempfile

def _need(mod):
    try:
        return __import__(mod)
    except ModuleNotFoundError:
        sys.exit(f"Missing dependency '{mod}'. Install: "
                 "pip install pypdf pdfplumber reportlab pytesseract pdf2image")

def cmd_info(a):
    pypdf = _need("pypdf")
    r = pypdf.PdfReader(a.input)
    enc = r.is_encrypted
    if enc:
        try:
            r.decrypt(getattr(a, "password", None) or "")
        except Exception:
            pass
    print(f"file:      {a.input}")
    print(f"encrypted: {enc}")
    size = None
    try:
        print(f"pages:     {len(r.pages)}")
        p = r.pages[0].mediabox
        size = f"{float(p.width):.0f} x {float(p.height):.0f} pt"
    except Exception:
        print("pages:     ? (locked — pass --password)")
    try:
        for k in ("/Title", "/Author", "/Subject", "/Creator", "/Producer"):
            if (r.metadata or {}).get(k):
                print(f"{k[1:]:9}: {r.metadata.get(k)}")
    except Exception:
        pass
    if size:
        print(f"page size: {size}")

def cmd_merge(a):
    pypdf = _need("pypdf")
    w = pypdf.PdfWriter()
    for f in a.inputs:
        for pg in pypdf.PdfReader(f).pages:
            w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"merged {len(a.inputs)} file(s) -> {a.output}")

def _parse_ranges(spec, n):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bits = part.split("-")
            if len(bits) != 2 or not bits[0] or not bits[1]:
                raise ValueError(f"invalid range '{part}'")
            lo, hi = int(bits[0]), int(bits[1])
            if lo > hi:
                raise ValueError(f"invalid descending range '{part}'")
            out.append(range(lo, hi + 1))
        else:
            page = int(part)
            out.append(range(page, page + 1))
    if not out:
        raise ValueError("no valid page ranges given")
    for rng in out:
        pages = list(rng)
        if not pages or pages[0] < 1 or pages[-1] > n:
            raise ValueError(f"range {pages[0]}-{pages[-1]} outside document pages 1-{n}")
    return out  # 1-based inclusive ranges

def cmd_split(a):
    pypdf = _need("pypdf")
    r = pypdf.PdfReader(a.input)
    n = len(r.pages)
    outdir = pathlib.Path(a.out_dir or "."); outdir.mkdir(parents=True, exist_ok=True)
    stem = pathlib.Path(a.input).stem
    try:
        groups = _parse_ranges(a.ranges, n) if a.ranges else [range(i, i + 1) for i in range(1, n + 1)]
    except ValueError as exc:
        sys.exit(f"Invalid page range: {exc}")
    for idx, rng in enumerate(groups, 1):
        w = pypdf.PdfWriter()
        for p in rng:
            w.add_page(r.pages[p - 1])
        out = outdir / f"{stem}_part{idx:02d}.pdf"
        with open(out, "wb") as fh:
            w.write(fh)
        print(f"  -> {out}")

def cmd_rotate(a):
    pypdf = _need("pypdf")
    r = pypdf.PdfReader(a.input); w = pypdf.PdfWriter()
    pages = set(_p for rng in (_parse_ranges(a.pages, len(r.pages)) if a.pages else []) for _p in rng)
    for i, pg in enumerate(r.pages, 1):
        if not pages or i in pages:
            pg.rotate(a.angle)
        w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"rotated {a.angle}° -> {a.output}")

def cmd_watermark(a):
    pypdf = _need("pypdf"); _need("reportlab")
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color
    import io
    r = pypdf.PdfReader(a.input)

    # Build one stamp per distinct page size so mixed-size / landscape pages each get a
    # correctly centered watermark (a single page[0]-sized stamp mis-places on the rest).
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
        if key not in stamps:
            stamps[key] = stamp_for(*key)
        pg.merge_page(stamps[key]); w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"watermarked '{a.text}' -> {a.output}")

def cmd_encrypt(a):
    pypdf = _need("pypdf")
    r = pypdf.PdfReader(a.input); w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.encrypt(user_password=a.password, owner_password=a.owner or a.password)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"encrypted -> {a.output}")

def cmd_decrypt(a):
    pypdf = _need("pypdf")
    r = pypdf.PdfReader(a.input)
    if r.is_encrypted:
        # decrypt() returns PasswordType.NOT_DECRYPTED (0/falsy) on a wrong password;
        # fail loudly instead of silently writing an empty/garbage PDF.
        if not r.decrypt(a.password):
            sys.exit("decrypt failed: wrong password (or unsupported encryption).")
    w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"decrypted -> {a.output}")

def cmd_metadata(a):
    pypdf = _need("pypdf")
    r = pypdf.PdfReader(a.input)
    if not a.set:
        for k, v in (r.metadata or {}).items():
            print(f"{k}: {v}")
        return
    if not a.output and not a.in_place:
        sys.exit("metadata --set requires --output OUT.pdf or explicit --in-place")
    w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.add_metadata({f"/{k}": v for k, v in (kv.split("=", 1) for kv in a.set)})
    out = pathlib.Path(a.output or a.input)
    if a.in_place:
        tmp = tempfile.NamedTemporaryFile(
            prefix=f"{out.name}.",
            suffix=".tmp",
            dir=str(out.parent or pathlib.Path(".")),
            delete=False,
        )
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

def cmd_extract_text(a):
    if a.layout and shutil.which("pdftotext"):
        txt = subprocess.run(["pdftotext", "-layout", a.input, "-"], capture_output=True, text=True).stdout
    else:
        pypdf = _need("pypdf")
        txt = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(a.input).pages)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print(f"text -> {a.out} ({len(txt)} chars)")
    else:
        print(txt)

def cmd_extract_tables(a):
    pdfplumber = _need("pdfplumber"); import csv
    rows = []
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

def cmd_ocr(a):
    _need("pytesseract"); _need("pdf2image")
    import pytesseract
    from pdf2image import convert_from_path
    if not shutil.which("tesseract"):
        sys.exit("tesseract not installed (apt install tesseract-ocr tesseract-ocr-vie).")
    pages = convert_from_path(a.input, dpi=a.dpi)
    txt = "\n\n".join(pytesseract.image_to_string(im, lang=a.lang) for im in pages)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print(f"ocr ({a.lang}) -> {a.out} ({len(txt)} chars)")
    else:
        print(txt)

def cmd_to_images(a):
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not installed (apt install poppler-utils).")
    outdir = pathlib.Path(a.out_dir or "."); outdir.mkdir(parents=True, exist_ok=True)
    prefix = str(outdir / pathlib.Path(a.input).stem)
    subprocess.run(["pdftoppm", "-png", "-r", str(a.dpi), a.input, prefix], check=True)
    print(f"images -> {outdir}/ (dpi {a.dpi})")

def main():
    ap = argparse.ArgumentParser(description="pdfx — PDF processing CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("info"); sp.set_defaults(fn=cmd_info); sp.add_argument("input"); sp.add_argument("--password")
    sp = sub.add_parser("merge"); sp.set_defaults(fn=cmd_merge); sp.add_argument("output"); sp.add_argument("inputs", nargs="+")
    sp = sub.add_parser("split"); sp.set_defaults(fn=cmd_split); sp.add_argument("input"); sp.add_argument("--ranges"); sp.add_argument("--out-dir")
    sp = sub.add_parser("rotate"); sp.set_defaults(fn=cmd_rotate); sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--angle", type=int, default=90); sp.add_argument("--pages")
    sp = sub.add_parser("watermark"); sp.set_defaults(fn=cmd_watermark); sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--text", required=True); sp.add_argument("--opacity", type=float, default=0.12); sp.add_argument("--size", type=int, default=72)
    sp = sub.add_parser("encrypt"); sp.set_defaults(fn=cmd_encrypt); sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--password", required=True); sp.add_argument("--owner")
    sp = sub.add_parser("decrypt"); sp.set_defaults(fn=cmd_decrypt); sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--password", required=True)
    sp = sub.add_parser("metadata"); sp.set_defaults(fn=cmd_metadata); sp.add_argument("input"); sp.add_argument("--set", nargs="*"); sp.add_argument("--output"); sp.add_argument("--in-place", action="store_true", help="overwrite input via atomic temp-file replace")
    sp = sub.add_parser("extract-text"); sp.set_defaults(fn=cmd_extract_text); sp.add_argument("input"); sp.add_argument("--out"); sp.add_argument("--layout", action="store_true")
    sp = sub.add_parser("extract-tables"); sp.set_defaults(fn=cmd_extract_tables); sp.add_argument("input"); sp.add_argument("--out")
    sp = sub.add_parser("ocr"); sp.set_defaults(fn=cmd_ocr); sp.add_argument("input"); sp.add_argument("--out"); sp.add_argument("--lang", default="eng"); sp.add_argument("--dpi", type=int, default=300)
    sp = sub.add_parser("to-images"); sp.set_defaults(fn=cmd_to_images); sp.add_argument("input"); sp.add_argument("--out-dir"); sp.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
