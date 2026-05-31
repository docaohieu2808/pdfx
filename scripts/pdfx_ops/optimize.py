"""Size & structure ops: compress (ghostscript), linearize (web-optimize),
pdfa (archival PDF/A), repair (rebuild a broken/bloated file)."""
import glob, pathlib, tempfile
from . import _util


def cmd_compress(a):
    """Shrink via ghostscript. quality: screen<ebook<printer<prepress (size↑ quality↑)."""
    _util.need_tool("gs", "ghostscript")
    before = _util.kb(a.input)
    _util.run(["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.6",
               f"-dPDFSETTINGS=/{a.quality}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
               f"-sOutputFile={a.output}", a.input])
    after = _util.kb(a.output)
    pct = (1 - after / before) * 100 if before else 0
    print(f"compressed /{a.quality}: {before} KB -> {after} KB ({pct:.0f}% smaller) -> {a.output}")


def cmd_linearize(a):
    """Linearize ('fast web view') so viewers can stream page 1 before full download."""
    _util.need_tool("qpdf")
    _util.run(["qpdf", "--linearize", a.input, a.output])
    print(f"linearized -> {a.output}")


def cmd_pdfa(a):
    """Convert to PDF/A-2b (archival) via ghostscript + a PDFA definition file."""
    _util.need_tool("gs", "ghostscript")
    defs = glob.glob("/usr/share/ghostscript/*/lib/PDFA_def.ps") + \
        glob.glob("/usr/share/ghostscript/*/Resource/Init/PDFA_def.ps")
    if defs:
        def_ps = defs[0]
    else:  # minimal inline definition
        tmp = tempfile.NamedTemporaryFile("w", suffix=".ps", delete=False)
        tmp.write("[ /Title (doc) /DOCINFO pdfmark\n")
        tmp.close()
        def_ps = tmp.name
    _util.run(["gs", "-dPDFA=2", "-dBATCH", "-dNOPAUSE", "-dQUIET",
               "-sColorConversionStrategy=RGB", "-sDEVICE=pdfwrite",
               "-dPDFACompatibilityPolicy=1", f"-sOutputFile={a.output}", def_ps, a.input])
    print(f"PDF/A-2b -> {a.output}")


def cmd_repair(a):
    """Rebuild a corrupt/bloated PDF. Tries mutool clean, falls back to qpdf rewrite."""
    import shutil
    if shutil.which("mutool"):
        _util.run(["mutool", "clean", "-ggg", "-d", a.input, a.output])
    elif shutil.which("qpdf"):
        _util.run(["qpdf", a.input, a.output])
    else:
        _util.sys.exit("need mutool (mupdf-tools) or qpdf to repair")
    print(f"repaired/rebuilt -> {a.output}")


def register(sub):
    sp = sub.add_parser("compress", help="shrink file size (ghostscript)"); sp.set_defaults(fn=cmd_compress)
    sp.add_argument("input"); sp.add_argument("output")
    sp.add_argument("--quality", default="ebook", choices=["screen", "ebook", "printer", "prepress"])
    sp = sub.add_parser("linearize", help="web-optimize (fast web view)"); sp.set_defaults(fn=cmd_linearize)
    sp.add_argument("input"); sp.add_argument("output")
    sp = sub.add_parser("pdfa", help="convert to archival PDF/A-2b"); sp.set_defaults(fn=cmd_pdfa)
    sp.add_argument("input"); sp.add_argument("output")
    sp = sub.add_parser("repair", help="rebuild a broken/bloated PDF"); sp.set_defaults(fn=cmd_repair)
    sp.add_argument("input"); sp.add_argument("output")
