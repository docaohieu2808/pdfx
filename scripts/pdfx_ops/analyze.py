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
    if a.mode == "text":
        return _compare_text(a)
    return _compare_visual(a)


def _compare_text(a):
    """Unified text diff of the two PDFs (content, not pixels)."""
    import subprocess, difflib

    def text(p):
        if shutil.which("pdftotext"):
            return subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True).stdout
        pypdf = _util.need("pypdf")
        return "\n".join(pg.extract_text() or "" for pg in pypdf.PdfReader(p).pages)

    diff = list(difflib.unified_diff(text(a.a).splitlines(), text(a.b).splitlines(),
                                     fromfile=a.a, tofile=a.b, lineterm=""))
    if not diff:
        print("-- text is identical")
        return
    print("\n".join(diff[:400]))
    if len(diff) > 400:
        print(f"… (+{len(diff) - 400} more diff lines)")


def _compare_visual(a):
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


def cmd_validate(a):
    """Validate a PDF against PDF/A with veraPDF (exit 1 if non-compliant)."""
    import re
    vp = _util.verapdf_path()
    if not vp:
        _util.sys.exit("veraPDF not found — run pdfx/install.sh (installs to ~/.local/share/verapdf).")
    ok, summary = _util.verapdf_validate(a.input, a.flavour)
    print(f"PDF/A-{a.flavour}: {'PASS ✅' if ok else 'FAIL ❌'}  — {summary}")
    if not ok and a.details:
        r = subprocess.run([vp, "-f", a.flavour, a.input], capture_output=True, text=True)
        fails = []
        for chunk in r.stdout.split("<rule"):
            if 'status="failed"' in chunk:
                cl = re.search(r'clause="([^"]+)"', chunk)
                tn = re.search(r'testNumber="([^"]+)"', chunk)
                if cl:
                    fails.append(f'{cl.group(1)}#{tn.group(1) if tn else "?"}')
        for f in list(dict.fromkeys(fails))[:12]:
            print(f"  failed clause {f}")
    if not ok:
        _util.sys.exit(1)


def register(sub):
    sp = sub.add_parser("info", help="page count, size, metadata, encryption"); sp.set_defaults(fn=cmd_info)
    sp.add_argument("input"); sp.add_argument("--password")
    sp = sub.add_parser("compare", help="diff two PDFs (visual pixels or text)"); sp.set_defaults(fn=cmd_compare)
    sp.add_argument("a"); sp.add_argument("b"); sp.add_argument("--out-dir", default="pdf-diff")
    sp.add_argument("--dpi", type=int, default=100); sp.add_argument("--mode", default="visual", choices=["visual", "text"])
    sp = sub.add_parser("validate", help="validate PDF/A conformance with veraPDF"); sp.set_defaults(fn=cmd_validate)
    sp.add_argument("input"); sp.add_argument("--flavour", default="2b", help="PDF/A flavour: 1b,2b,3b,2u,…")
    sp.add_argument("--details", action="store_true", help="list failed clauses on FAIL")
