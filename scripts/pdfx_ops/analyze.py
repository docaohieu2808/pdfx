"""Inspection ops: info (rich summary), compare (page-by-page visual diff)."""
import shutil, subprocess, pathlib
from . import _util


def cmd_info(a):
    """Rich summary: prefer poppler pdfinfo, enrich with pypdf metadata."""
    if shutil.which("pdfinfo"):
        cmd = ["pdfinfo", a.input]
        if a.password:
            cmd[1:1] = ["-upw", a.password]
        subprocess.run(cmd)
        return
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    print(f"file:      {a.input}")
    print(f"encrypted: {r.is_encrypted}")
    if r.is_encrypted and a.password:
        r.decrypt(a.password)
    try:
        print(f"pages:     {len(r.pages)}")
    except Exception:
        print("pages:     ? (locked — pass --password)")
    for k, v in (r.metadata or {}).items():
        print(f"{k}: {v}")


def cmd_compare(a):
    """Render both PDFs and report per-page visual differences (PIL pixel diff)."""
    _util.need_tool("pdftoppm", "poppler-utils")
    Image = _util.need("PIL")
    from PIL import Image, ImageChops
    import tempfile

    def render(path, d):
        prefix = str(pathlib.Path(d) / "p")
        _util.run(["pdftoppm", "-png", "-r", str(a.dpi), path, prefix],
                  capture_output=True, text=True)
        return sorted(pathlib.Path(d).glob("p*.png"))

    outdir = _util.out_dir(a.out_dir)
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        A, B = render(a.a, d1), render(a.b, d2)
        if len(A) != len(B):
            print(f"page count differs: {a.a}={len(A)}  {a.b}={len(B)}")
        diffs = 0
        for i in range(min(len(A), len(B))):
            ia, ib = Image.open(A[i]).convert("RGB"), Image.open(B[i]).convert("RGB")
            if ia.size != ib.size:
                ib = ib.resize(ia.size)
            bbox = ImageChops.difference(ia, ib).getbbox()
            if bbox:
                diffs += 1
                dimg = ImageChops.difference(ia, ib)
                dimg.save(outdir / f"diff_p{i+1:02d}.png")
                print(f"page {i+1}: DIFFERS (region {bbox})")
            else:
                print(f"page {i+1}: identical")
        print(f"-- {diffs} differing page(s); diff images -> {outdir}/" if diffs
              else "-- documents are visually identical")


def register(sub):
    sp = sub.add_parser("info", help="page count, size, metadata, encryption"); sp.set_defaults(fn=cmd_info)
    sp.add_argument("input"); sp.add_argument("--password")
    sp = sub.add_parser("compare", help="visual page-by-page diff of two PDFs"); sp.set_defaults(fn=cmd_compare)
    sp.add_argument("a"); sp.add_argument("b"); sp.add_argument("--out-dir", default="pdf-diff"); sp.add_argument("--dpi", type=int, default=100)
