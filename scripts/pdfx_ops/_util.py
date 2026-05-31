"""Shared helpers for pdfx_ops modules: dependency guard, on-demand install,
page-range parsing, subprocess runner, tool discovery."""
import os, sys, shutil, subprocess, pathlib


def need(mod):
    """Import a Python dependency or exit with an install hint."""
    try:
        return __import__(mod)
    except ModuleNotFoundError:
        sys.exit(f"Missing dependency '{mod}'. Install with the skills venv:\n"
                 "  pip install pypdf pikepdf pymupdf pdfplumber reportlab img2pdf "
                 "pytesseract pdf2image weasyprint  (or run pdfx/install.sh)")


def ensure(import_name, pip_name=None):
    """Import a Python package, auto pip-installing it into THIS venv on first use
    (the 'use it → grab what's missing' model). Set PDFX_NO_AUTOINSTALL=1 to disable."""
    try:
        return __import__(import_name)
    except ModuleNotFoundError:
        pass
    pkg = pip_name or import_name
    if os.environ.get("PDFX_NO_AUTOINSTALL"):
        sys.exit(f"Missing '{import_name}'. Run: pip install {pkg}  (or pdfx/install.sh)")
    print(f"[pdfx] '{import_name}' missing — installing {pkg} into the venv…", file=sys.stderr)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=False)
    try:
        return __import__(import_name)
    except ModuleNotFoundError:
        sys.exit(f"Could not auto-install {pkg}; install it manually or run pdfx/install.sh")


def need_tool(name, apt=None):
    """Ensure a system CLI exists or exit with an apt hint."""
    if not shutil.which(name):
        hint = f" (apt install {apt})" if apt else ""
        sys.exit(f"Required tool '{name}' not found{hint}.")
    return name


def run(cmd, **kw):
    """Run a command, raising a clean error on failure."""
    try:
        return subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Command failed ({exc.returncode}): {' '.join(map(str, cmd))}\n{exc.stderr or ''}")


def parse_pages(spec, n):
    """'1-3,5,8-9' -> sorted unique 1-based page list, validated against n pages."""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-")
            lo, hi = int(lo), int(hi)
            if lo > hi:
                sys.exit(f"Invalid descending range '{part}'")
            out.extend(range(lo, hi + 1))
        else:
            out.append(int(part))
    if not out:
        sys.exit("No valid pages given")
    for p in out:
        if p < 1 or p > n:
            sys.exit(f"Page {p} outside document range 1-{n}")
    return out  # order preserved (allows reordering), may contain dups


def parse_groups(spec, n):
    """'1-3,4-6' -> list of 1-based inclusive page-range groups (for split)."""
    groups = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-"))
            if lo > hi:
                sys.exit(f"Invalid descending range '{part}'")
            groups.append(list(range(lo, hi + 1)))
        else:
            p = int(part)
            groups.append([p])
    for g in groups:
        if g[0] < 1 or g[-1] > n:
            sys.exit(f"Range {g[0]}-{g[-1]} outside document range 1-{n}")
    return groups


def verapdf_path():
    """Locate the veraPDF CLI (PATH, ~/.local/share/verapdf, /opt/verapdf)."""
    p = shutil.which("verapdf")
    if p:
        return p
    for c in (pathlib.Path.home() / ".local/share/verapdf" / "verapdf",
              pathlib.Path("/opt/verapdf/verapdf")):
        if c.is_file():
            return str(c)
    return None


def verapdf_validate(path, flavour="2b"):
    """Validate against PDF/A. Returns (compliant: bool|None, one-line summary).
    None means veraPDF is not installed."""
    vp = verapdf_path()
    if not vp:
        return None, "veraPDF not installed — run pdfx/install.sh"
    r = subprocess.run([vp, "-f", flavour, "--format", "text", path],
                       capture_output=True, text=True)
    out = (r.stdout or r.stderr).strip().splitlines()
    line = out[0] if out else ""
    return line.startswith("PASS"), line


def out_dir(path):
    d = pathlib.Path(path or ".")
    d.mkdir(parents=True, exist_ok=True)
    return d


def kb(path):
    return pathlib.Path(path).stat().st_size // 1024
