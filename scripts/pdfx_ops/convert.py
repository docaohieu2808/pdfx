"""Create PDFs from other formats: from-images (img2pdf, lossless),
from-html (local file), from-url (live web page)."""
from . import _util


def cmd_from_images(a):
    img2pdf = _util.need("img2pdf")
    with open(a.output, "wb") as fh:
        fh.write(img2pdf.convert(a.images))
    print(f"images -> {a.output} ({len(a.images)} page(s))")


def cmd_from_html(a):
    _util.need("weasyprint")
    from weasyprint import HTML
    import pathlib
    src = pathlib.Path(a.input).resolve()
    HTML(filename=str(src), base_url=str(src.parent)).write_pdf(a.output)
    print(f"html -> {a.output}")


def cmd_from_url(a):
    _util.need("weasyprint")
    from weasyprint import HTML
    HTML(url=a.url).write_pdf(a.output)
    print(f"url -> {a.output}")


def register(sub):
    sp = sub.add_parser("from-images", help="combine images into a PDF"); sp.set_defaults(fn=cmd_from_images)
    sp.add_argument("output"); sp.add_argument("images", nargs="+")
    sp = sub.add_parser("from-html", help="render a local HTML file to PDF"); sp.set_defaults(fn=cmd_from_html)
    sp.add_argument("input"); sp.add_argument("output")
    sp = sub.add_parser("from-url", help="render a live web page to PDF"); sp.set_defaults(fn=cmd_from_url)
    sp.add_argument("url"); sp.add_argument("output")
