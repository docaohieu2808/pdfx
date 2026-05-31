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


ICC_CANDIDATES = [
    "/usr/share/color/icc/ghostscript/srgb.icc",
    "/usr/share/color/icc/sRGB.icc",
    "/usr/share/texlive/texmf-dist/tex/generic/colorprofiles/sRGB.icc",
    "/usr/share/ghostscript/*/iccprofiles/default_rgb.icc",
    "/System/Library/ColorSync/Profiles/sRGB Profile.icc",
]
PDFA_DEF = """%%!
[/_objdef {icc_PDFA} /type /stream /OBJ pdfmark
[{icc_PDFA} <</N 3 /Alternate /DeviceRGB>> /PUT pdfmark
[{icc_PDFA} (%s) (r) file /PUT pdfmark
[/_objdef {OutputIntent_PDFA} /type /dict /OBJ pdfmark
[{OutputIntent_PDFA} <<
  /Type /OutputIntent /S /GTS_PDFA1
  /DestOutputProfile {icc_PDFA}
  /OutputConditionIdentifier (sRGB) /Info (sRGB IEC61966-2.1)
>> /PUT pdfmark
[{Catalog} <</OutputIntents [ {OutputIntent_PDFA} ]>> /PUT pdfmark
"""


def _find_icc():
    for pat in ICC_CANDIDATES:
        for p in glob.glob(pat):
            if pathlib.Path(p).is_file():
                return p
    return None


def cmd_pdfa(a):
    """Convert to archival PDF/A-2b via ghostscript with a proper sRGB OutputIntent
    (validates against veraPDF). Pass --validate to check the result with veraPDF."""
    _util.need_tool("gs", "ghostscript")
    icc = _find_icc()
    base = ["gs", "-dPDFA=2", "-dBATCH", "-dNOPAUSE", "-dQUIET",
            "-sProcessColorModel=DeviceRGB", "-sColorConversionStrategy=RGB",
            "-sDEVICE=pdfwrite", "-dPDFACompatibilityPolicy=1", f"-sOutputFile={a.output}"]
    if icc:
        defps = tempfile.NamedTemporaryFile("w", suffix=".ps", delete=False)
        defps.write(PDFA_DEF % icc)
        defps.close()
        _util.run(base + [f"--permit-file-read={icc}", defps.name, a.input])
        pathlib.Path(defps.name).unlink(missing_ok=True)
    else:
        print("[pdfa] no sRGB ICC profile found — producing best-effort PDF/A (may not "
              "validate). Install ghostscript color profiles / run install.sh.")
        _util.run(base + [a.input])
    print(f"PDF/A-2b -> {a.output}")
    if a.validate:
        ok, summary = _util.verapdf_validate(a.output, "2b")
        print(f"  veraPDF: {summary}" if ok is not None else f"  {summary}")


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
    sp = sub.add_parser("pdfa", help="convert to archival PDF/A-2b (veraPDF-valid)"); sp.set_defaults(fn=cmd_pdfa)
    sp.add_argument("input"); sp.add_argument("output")
    sp.add_argument("--validate", action="store_true", help="check the result with veraPDF")
    sp = sub.add_parser("repair", help="rebuild a broken/bloated PDF"); sp.set_defaults(fn=cmd_repair)
    sp.add_argument("input"); sp.add_argument("output")
