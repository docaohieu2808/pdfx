#!/usr/bin/env python3
"""Build a publication-quality PDF ebook/report from Markdown via WeasyPrint.

Markdown -> HTML (python-markdown + Pygments) -> WeasyPrint -> PDF, with a designed
cover, auto-numbered TOC, syntax-highlighted code, PDF bookmarks, [B]/[I]/[A]/[!]
badges, and (this build) inline-SVG support, ```mermaid rendering, part dividers,
depth-2 TOC, an A-Z index, and optional auto-preview.

Run with the skills venv:
  python build_ebook_from_markdown.py --title "My Handbook" --output book.pdf \
      --page a4 --theme light --accent "#2563eb" --gen-cover "idea" \
      --parts "1=Foundations,7=Build & Ship" --toc-depth 2 --index --preview \
      file1.md file2.md ...

Each file's first H1 = chapter title (removed from the body). --input-dir DIR takes
all *.md (sorted). Diagrams: write inline <svg>…</svg> OR a ```mermaid fence.
"""
import argparse, html, pathlib, datetime, sys, subprocess

try:
    import markdown
    from weasyprint import HTML
except ModuleNotFoundError as exc:
    sys.exit(f"Missing dependency: {exc.name}. pip install weasyprint markdown pygments")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pdfx_lib import cover as cover_mod, markdown_render as mr, toc_index as ti, styles


def parse_parts(spec):
    parts = {}
    if not spec:
        return parts
    for item in spec.split(","):
        if "=" in item:
            num, title = item.split("=", 1)
            parts[int(num)] = title.strip()
    return parts


def main():
    ap = argparse.ArgumentParser(description="Build a designed PDF ebook from Markdown.")
    ap.add_argument("files", nargs="*", help="Markdown files in chapter order")
    ap.add_argument("--input-dir", help="Use all *.md in this dir (sorted)")
    ap.add_argument("--output", default="ebook.pdf")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--kicker", default="A FIELD HANDBOOK")
    ap.add_argument("--stats", default="")
    ap.add_argument("--cover-image", help="pre-made cover background image")
    ap.add_argument("--gen-cover", metavar="IDEA", help="auto-generate cover via Gemini")
    ap.add_argument("--page", choices=["a4", "6x9"], default="a4")
    ap.add_argument("--theme", choices=["light", "dark"], default="light")
    ap.add_argument("--accent", default="#2563eb")
    ap.add_argument("--parts", help="part dividers: '1=Title,7=Title2' (before chapter N)")
    ap.add_argument("--toc-depth", type=int, default=1, choices=[1, 2], help="1=chapters, 2=+ H2")
    ap.add_argument("--index", action="store_true", help="append an A-Z index (bold table terms + [[term]])")
    ap.add_argument("--preview", action="store_true", help="render page PNGs after build")
    args = ap.parse_args()

    if args.input_dir:
        d = pathlib.Path(args.input_dir)
        if not d.is_dir():
            sys.exit(f"Input directory not found: {d}")
        paths = sorted(d.glob("*.md"))
    else:
        paths = [pathlib.Path(f) for f in args.files]
    paths = [p for p in paths if p.name.lower() != "readme.md"]
    if not paths:
        sys.exit("No Markdown files given (use files... or --input-dir).")
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        sys.exit("Markdown file(s) not found:\n  " + "\n  ".join(missing))

    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "codehilite", "attr_list", "sane_lists", "md_in_html"],
        extension_configs={"codehilite": {"guess_lang": False}})
    base = pathlib.Path(args.output).resolve().parent
    assets = base / "_pdfx_assets"

    cover_rel = None
    if args.gen_cover:
        cover_rel = cover_mod.generate_cover(args.gen_cover, base / "cover-generated.png", args.theme)
    if cover_rel is None and args.cover_image:
        cover_rel = pathlib.Path(args.cover_image).resolve()
        if not cover_rel.is_file():
            sys.exit(f"Cover image not found: {cover_rel}")

    css = styles.build_css(args.theme, args.page, args.accent, cover_rel)
    ids = mr.chapter_ids(paths)
    parts = parse_parts(args.parts)

    chapters_html, chapters_info, term_map = [], [], {}
    for i, p in enumerate(paths, 1):
        if i in parts:
            chapters_html.append(ti.part_divider_html(parts[i], i))
        section, title, subs = mr.render_chapter(md, p, i, ids[p], assets, args.toc_depth)
        chapters_html.append(section)
        chapters_info.append((i, title, ids[p], subs))
        if args.index:
            for term in ti.extract_terms(p.read_text(encoding="utf-8")):
                term_map.setdefault(term, set()).add(i)

    toc_rows = ti.build_toc(chapters_info, parts, args.toc_depth)
    index_html = ti.build_index(term_map) if args.index else ""
    today = datetime.date.today().isoformat()
    stats = args.stats or f"{len(paths)} CHAPTERS"

    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>
<section class="cover"><div class="scrim-top"></div><div class="scrim-bot"></div>
  <div class="mid"><div class="kick">{html.escape(args.kicker)}</div><div class="bar"></div>
    <h1>{html.escape(args.title)}</h1>
    <div class="sub">{html.escape(args.subtitle)}</div></div>
  <div class="foot"><div class="stats">{html.escape(stats)}</div>{today}</div>
</section>
<nav class="toc"><h1>Table of Contents</h1><hr><ol>{toc_rows}</ol></nav>
{''.join(chapters_html)}{index_html}</body></html>"""

    out = pathlib.Path(args.output)
    out.with_suffix(".debug.html").write_text(doc, encoding="utf-8")
    HTML(string=doc, base_url=str(base)).write_pdf(str(out))
    print(f"PDF: {out.resolve()}  ({out.stat().st_size // 1024} KB, {len(paths)} chapters)")

    if args.preview:
        pv = out.with_name(out.stem + "_preview")
        pv.mkdir(exist_ok=True)
        try:
            subprocess.run(["pdftoppm", "-png", "-r", "90", str(out), str(pv / "page")], check=True)
            n = len(list(pv.glob("page*.png")))
            print(f"preview: {n} page PNG(s) -> {pv}/  (Read them to visually validate)")
        except Exception as exc:
            print(f"preview skipped ({exc})")
    else:
        print("Tip: --preview to auto-render, or: pdftoppm -png -r 150 -f 1 -l 1", out, "prev")


if __name__ == "__main__":
    main()
