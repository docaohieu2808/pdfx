"""Security & privacy ops: encrypt, decrypt, unlock (strip restrictions),
redact (true content removal), permissions (inspect)."""
import pathlib
from . import _util


def cmd_encrypt(a):
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.encrypt(user_password=a.password, owner_password=a.owner or a.password)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"encrypted -> {a.output}")


def cmd_decrypt(a):
    pypdf = _util.need("pypdf")
    r = pypdf.PdfReader(a.input)
    if r.is_encrypted:
        if not r.decrypt(a.password):
            _util.sys.exit("decrypt failed: wrong password (or unsupported encryption).")
    w = pypdf.PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    with open(a.output, "wb") as fh:
        w.write(fh)
    print(f"decrypted -> {a.output}")


def cmd_unlock(a):
    """Strip owner-password restrictions (print/copy/edit) via qpdf --decrypt."""
    _util.need_tool("qpdf")
    cmd = ["qpdf", "--decrypt"]
    if a.password:
        cmd.append(f"--password={a.password}")
    cmd += [a.input, a.output]
    _util.run(cmd)
    print(f"unlocked (restrictions removed) -> {a.output}")


def cmd_redact(a):
    """Permanently remove content. --text redacts every match (--ignore-case / --regex
    widen matching, word-level); --rects 'p:x0,y0,x1,y1' redacts boxes (page 1-based).
    Redacted areas are filled black and the underlying text removed."""
    import re
    fitz = _util.need("fitz")
    doc = fitz.open(a.input)
    hits = 0
    if a.text and (a.regex or a.ignore_case):
        pat = re.compile(a.text if a.regex else re.escape(a.text),
                         re.IGNORECASE if a.ignore_case else 0)
        for page in doc:
            for w in page.get_text("words"):  # (x0,y0,x1,y1,word,...)
                if pat.search(w[4]):
                    page.add_redact_annot(fitz.Rect(w[:4]), fill=(0, 0, 0))
                    hits += 1
    elif a.text:  # exact phrase (handles multi-word spans)
        for page in doc:
            for rect in page.search_for(a.text):
                page.add_redact_annot(rect, fill=(0, 0, 0))
                hits += 1
    for spec in (a.rects or []):
        pg_s, coords = spec.split(":")
        x0, y0, x1, y1 = (float(v) for v in coords.split(","))
        page = doc[int(pg_s) - 1]
        page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=(0, 0, 0))
        hits += 1
    for page in doc:
        page.apply_redactions()
    doc.save(a.output, garbage=4, deflate=True)
    print(f"redacted {hits} area(s) -> {a.output}")


def cmd_permissions(a):
    """Inspect encryption + permission flags."""
    pikepdf = _util.need("pikepdf")
    try:
        pdf = pikepdf.open(a.input, password=a.password or "")
    except pikepdf.PasswordError:
        _util.sys.exit("locked — pass --password")
    enc = pdf.encryption
    print(f"encrypted: {bool(enc)}")
    if enc:
        print(f"  method: R{enc.R} ({enc.bits}-bit)")
        p = pdf.allow
        for flag in ("accessibility", "extract", "modify_annotation", "modify_assembly",
                     "modify_form", "modify_other", "print_lowres", "print_highres"):
            print(f"  {flag:20}: {getattr(p, flag)}")


def register(sub):
    sp = sub.add_parser("encrypt", help="add a password"); sp.set_defaults(fn=cmd_encrypt)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--password", required=True); sp.add_argument("--owner")
    sp = sub.add_parser("decrypt", help="remove a known password"); sp.set_defaults(fn=cmd_decrypt)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--password", required=True)
    sp = sub.add_parser("unlock", help="strip owner restrictions (qpdf)"); sp.set_defaults(fn=cmd_unlock)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--password")
    sp = sub.add_parser("redact", help="permanently remove text/areas"); sp.set_defaults(fn=cmd_redact)
    sp.add_argument("input"); sp.add_argument("output"); sp.add_argument("--text"); sp.add_argument("--rects", nargs="*")
    sp.add_argument("--ignore-case", action="store_true"); sp.add_argument("--regex", action="store_true")
    sp = sub.add_parser("permissions", help="inspect encryption + permission flags"); sp.set_defaults(fn=cmd_permissions)
    sp.add_argument("input"); sp.add_argument("--password")
