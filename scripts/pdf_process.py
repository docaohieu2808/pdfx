#!/usr/bin/env python3
"""pdfx processing CLI — one entry point for every PDF operation.

Run with the skills venv. Groups (see `pdf_process.py -h` for all subcommands):
  transform : merge · split · rotate · pages · nup · crop
  extract   : extract-text · extract-tables · extract-images · to-images
              to-html · to-markdown · fonts · links · attachments · bookmarks
  security  : encrypt · decrypt · unlock · redact · permissions
  optimize  : compress · linearize · pdfa · repair
  annotate  : watermark · stamp · metadata
  convert   : from-images · from-html · from-url
  analyze   : info · compare
  ocr       : ocr · ocr-searchable

Examples:
  python pdf_process.py merge out.pdf a.pdf b.pdf
  python pdf_process.py compress big.pdf small.pdf --quality ebook
  python pdf_process.py redact in.pdf out.pdf --text "SECRET"
  python pdf_process.py compare v1.pdf v2.pdf
  python pdf_process.py ocr-searchable scan.pdf searchable.pdf --lang vie+eng

For form-filling use the dedicated scripts (check_fillable_fields.py, fill_fillable_fields.py).
For generating beautiful ebooks/reports use build_ebook_from_markdown.py.
"""
import argparse, sys, pathlib

# Allow running both as `python pdf_process.py` and as a module.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pdfx_ops import (analyze, extract, transform, security,
                      optimize, annotate, convert, ocr_ops)

MODULES = [transform, extract, security, optimize, annotate, convert, analyze, ocr_ops]


def main():
    ap = argparse.ArgumentParser(
        description="pdfx — comprehensive PDF processing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for mod in MODULES:
        mod.register(sub)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
