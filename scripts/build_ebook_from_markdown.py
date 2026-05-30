#!/usr/bin/env python3
"""Build a publication-quality PDF ebook from Markdown files via WeasyPrint.

Markdown -> HTML (python-markdown + Pygments) -> WeasyPrint -> PDF, with a designed
cover, auto-numbered Table of Contents (CSS target-counter), syntax-highlighted code,
PDF bookmarks, and [B]/[I]/[A]/[!] tag badges.

Run with the skills venv:
  python build_ebook_from_markdown.py \
      --title "My Handbook" --subtitle "Complete Reference" \
      --output book.pdf --page a4 --theme light --accent "#2563eb" \
      --cover-image cover.png  file1.md file2.md ...

Each Markdown file's first H1 becomes a chapter title; the H1 is removed from the body.
Use --input-dir DIR to take all *.md (sorted) instead of listing files.
"""
import argparse, re, html, pathlib, datetime, sys, os

try:
    import markdown
    from pygments.formatters import HtmlFormatter
    from weasyprint import HTML
except ModuleNotFoundError as exc:
    sys.exit(
        f"Missing Python dependency: {exc.name}. Install with:\n"
        "  pip install weasyprint markdown pygments\n"
        "Optional cover generation also needs:\n"
        "  pip install google-genai"
    )

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
FONTS = SKILL_DIR / "assets" / "fonts"

ENV_CANDIDATES = [
    SKILL_DIR / ".env",
    SKILL_DIR.parent / ".env",
    pathlib.Path.home() / ".agents/.env",
    pathlib.Path.home() / ".claude/.env",
]

def _gemini_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    for envfile in ENV_CANDIDATES:
        if envfile.exists():
            for line in envfile.read_text(errors="ignore").splitlines():
                if line.startswith("GEMINI_API_KEY") and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"')
    return None

def generate_cover(idea, out_path, theme):
    """Generate a flat, text-free cover via Gemini (Nano Banana) directly — pdfx depends
    on NO other skill, only the `google-genai` package + a GEMINI_API_KEY. Returns the
    path on success, or None to fall back to a CSS gradient cover (build still succeeds)."""
    key = _gemini_key()
    if not key:
        print("[gen-cover] no GEMINI_API_KEY (env or .env); using gradient cover.")
        return None
    try:
        from google import genai
        from google.genai import types
    except ModuleNotFoundError:
        print("[gen-cover] google-genai not installed (pip install google-genai); gradient cover.")
        return None
    tone = ("Bright airy near-white background, soft pastel blue and teal accents, premium minimal."
            if theme == "light" else
            "Deep dark navy background, glowing cyan and teal neon accents, premium minimal.")
    prompt = (f"Flat full-bleed 2D book-cover illustration that fills the entire frame, edge to edge. "
              f"{idea}. {tone} Modern flat isometric vector art, clean lines. "
              f"IMPORTANT: a flat artwork only — NOT a photo of a book, no 3D book mockup, no spine, "
              f"no page edges, no border, no drop shadow, and absolutely no text, letters or numbers.")
    print("[gen-cover] generating cover via Gemini Nano Banana (2:3, 2K)…")
    try:
        client = genai.Client(api_key=key)
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="2:3", image_size="2K"))
        resp = client.models.generate_content(
            model="gemini-3.1-flash-image-preview", contents=prompt, config=config)
        for part in resp.candidates[0].content.parts:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None)
            if data:
                # Honor the real returned image type — Gemini often returns JPEG, so
                # don't leave JPEG bytes under a .png name (WeasyPrint sniffs content
                # and renders either way, but the artifact should be labeled correctly).
                mime = (getattr(inline, "mime_type", "") or "").lower()
                if "jpeg" in mime or "jpg" in mime:
                    out_path = out_path.with_suffix(".jpg")
                elif "webp" in mime:
                    out_path = out_path.with_suffix(".webp")
                out_path.write_bytes(data)
                print(f"[gen-cover] ok -> {out_path}")
                return out_path
    except Exception as exc:
        print(f"[gen-cover] failed ({exc}); using gradient cover.")
        return None
    print("[gen-cover] no image returned; using gradient cover.")
    return None

TAG = re.compile(r'\[(B|I|A)\]')
GOTCHA = re.compile(r'\[!\]')

def badges(h):
    h = TAG.sub(lambda m: f'<span class="tag t-{m.group(1).lower()}">{m.group(1)}</span>', h)
    return GOTCHA.sub('<span class="tag t-warn">!</span>', h)

def first_h1(text, fallback="Untitled"):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def slugify(value, fallback):
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return slug or fallback


def chapter_ids(paths):
    seen = {}
    ids = {}
    for path in paths:
        base = slugify(path.stem, f"chapter-{len(ids) + 1}")
        count = seen.get(base, 0) + 1
        seen[base] = count
        ids[path] = base if count == 1 else f"{base}-{count}"
    return ids


def render_chapter(md, path, num, chapter_id):
    raw = path.read_text(encoding="utf-8")
    title = first_h1(raw, path.stem)
    # Strip the first top-level H1 line wherever it sits (mirrors first_h1's
    # startswith("# ")). Without MULTILINE this only fired when "# " was the very
    # first byte, so any file with a leading blank line / front-matter kept its H1
    # and the title rendered twice (once in the chapter header, once in the body).
    body_md = re.sub(r'^# .*\n?', '', raw, count=1, flags=re.MULTILINE)
    md.reset()
    body = badges(md.convert(body_md))
    return f'''<section class="chapter" id="ch-{chapter_id}">
  <header class="chap-head"><div class="chap-num">{num:02d}</div>
  <h1 class="chap-title">{html.escape(title)}</h1></header>
  {body}
</section>'''


def toc(paths, ids):
    rows = []
    for i, p in enumerate(paths, 1):
        t = first_h1(p.read_text(encoding="utf-8"), p.stem)
        rows.append(f'<li><a href="#ch-{ids[p]}"><span class="tnum">{i:02d}</span>'
                    f'<span class="tttl">{html.escape(t)}</span></a></li>')
    return "\n".join(rows)

def build_css(theme, page, accent, cover_image):
    size = "A4" if page == "a4" else "6in 9in"
    cover_height = "297mm" if page == "a4" else "9in"
    body_pt = "10pt" if page == "a4" else "11pt"
    dark = theme == "dark"
    ink   = "#e8eef5" if dark else "#1f2430"
    bg    = "#10151c" if dark else "#ffffff"
    muted = "#9aa6b4" if dark else "#5c6470"
    rule  = "#2a313c" if dark else "#d9dee6"
    code_bg = "#161c24" if dark else "#f6f8fa"
    cover_base = "#0f1722" if dark else "#f4f7fb"
    pyg = HtmlFormatter(style="dracula" if dark else "friendly").get_style_defs(".codehilite")
    # cover background: image (scrims keep title legible) or a gradient fallback
    if cover_image:
        cover_bg = f"{cover_base} url({cover_image}) center top/cover no-repeat"
    elif dark:
        cover_bg = "radial-gradient(130% 80% at 50% -15%,#1d3a52 0%,#0f2233 55%,#081523 100%)"
    else:
        cover_bg = f"linear-gradient(160deg,#ffffff 0%,#eaf1fb 60%,#dce8f7 100%)"
    title_color = "#13233a" if not dark else "#ffffff"
    sub_color = "#3a4757" if not dark else "#cdd9e6"
    foot_color = "#5c6470" if not dark else "#aebccd"
    scrim = "244,247,251" if not dark else "16,23,32"
    return f"""
@font-face{{font-family:'Display';src:url({FONTS}/PlayfairDisplay.ttf);font-weight:400 900}}
@font-face{{font-family:'Book';src:url({FONTS}/EBGaramond.ttf);font-weight:400 800}}
@page{{size:{size};margin:20mm 18mm 18mm;
  @top-center{{content:string(doctitle);font-family:'Inter',sans-serif;font-size:7pt;
    letter-spacing:2px;color:{muted}}}
  @bottom-center{{content:counter(page);font-family:'Inter',sans-serif;font-size:9pt;color:{muted}}}}}
@page cover{{margin:0;@top-center{{content:none}}@bottom-center{{content:none}}}}
@page nohead{{@top-center{{content:none}}}}
html{{font-family:'Inter','Lato',sans-serif;color:{ink};font-size:{body_pt};line-height:1.5}}
body{{margin:0;background:{bg}}}
h1,h2,h3,h4{{font-family:'Inter',sans-serif;line-height:1.2;color:{ink}}}
a{{color:{accent};text-decoration:none}} p{{margin:.2em 0 .7em}}
code,pre,kbd{{font-family:'JetBrains Mono','DejaVu Sans Mono',monospace}}

.cover{{page:cover;break-after:page;height:{cover_height};position:relative;color:{title_color};
  background:{cover_bg}}}
.cover .scrim-top{{position:absolute;top:0;left:0;right:0;height:160mm;
  background:linear-gradient(180deg,rgba({scrim},.99) 0%,rgba({scrim},.95) 40%,rgba({scrim},.6) 66%,rgba({scrim},0) 100%)}}
.cover .scrim-bot{{position:absolute;bottom:0;left:0;right:0;height:62mm;
  background:linear-gradient(0deg,rgba({scrim},.96) 0%,rgba({scrim},.6) 55%,rgba({scrim},0) 100%)}}
.cover .mid{{position:absolute;left:18mm;right:18mm;top:32mm;text-align:center}}
.cover .kick{{font-family:'Inter';letter-spacing:6px;font-size:10.5pt;color:{accent};font-weight:700}}
.cover .bar{{width:54px;height:3px;background:{accent};margin:8mm auto;border-radius:2px}}
.cover h1{{font-family:'Display';font-size:52pt;font-weight:800;color:{title_color};margin:0;line-height:1.04}}
.cover .sub{{font-family:'Book';font-style:italic;font-size:15pt;color:{sub_color};margin-top:7mm;line-height:1.4}}
.cover .foot{{position:absolute;left:18mm;right:18mm;bottom:20mm;text-align:center;
  font-family:'Inter';font-size:9pt;letter-spacing:2px;color:{foot_color}}}
.cover .stats{{font-family:'JetBrains Mono';font-size:8.5pt;color:{accent};margin-bottom:5mm;letter-spacing:1px;font-weight:600}}

nav.toc{{page:nohead;break-after:page}}
nav.toc>h1{{font-family:'Display';font-size:30pt;margin:0 0 4mm}}
nav.toc hr{{border:0;border-top:1px solid {rule};margin:4mm 0}}
nav.toc ol{{list-style:none;margin:0;padding:0}} nav.toc li{{margin:0 0 3.4mm}}
nav.toc a{{display:block;color:{ink};font-size:11pt}}
nav.toc .tnum{{font-family:'JetBrains Mono';font-size:8.5pt;color:{accent};display:inline-block;width:9mm}}
nav.toc a::after{{content:leader('. ') target-counter(attr(href),page);font-family:'Inter';font-size:9.5pt;color:{muted}}}

.chapter{{break-before:page}}
.chap-head{{border-bottom:2px solid {accent};padding-bottom:4mm;margin-bottom:7mm}}
.chap-num{{font-family:'JetBrains Mono';font-size:11pt;color:{accent};letter-spacing:2px}}
.chap-title{{font-family:'Display';font-size:27pt;font-weight:800;margin:1mm 0 0;string-set:doctitle content();
  bookmark-level:1;bookmark-label:content()}}
.chapter h2{{font-size:15pt;margin:7mm 0 2mm;padding-top:2mm;border-top:1px solid {rule};
  bookmark-level:2;bookmark-label:content()}}
.chapter h3{{font-size:12pt;color:{accent};margin:5mm 0 1mm}}
.chapter h4{{font-size:10.5pt;color:{muted};margin:4mm 0 1mm}}

.codehilite{{background:{code_bg};border:1px solid {rule};border-radius:5px;padding:5px 9px;
  margin:3mm 0;font-size:8.2pt;line-height:1.42}}
.codehilite pre{{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}}
:not(pre)>code{{background:{code_bg};border:1px solid {rule};border-radius:3px;padding:.5px 4px;font-size:8.6pt}}
{pyg}

table{{border-collapse:collapse;width:100%;margin:3mm 0;font-size:8.6pt}}
th,td{{border:1px solid {rule};padding:3px 7px;text-align:left;vertical-align:top}}
th{{background:{code_bg};font-family:'Inter';font-weight:700}}

.tag{{display:inline-block;font-family:'Inter';font-weight:700;font-size:7pt;padding:1px 5px;
  border-radius:9px;color:#fff;vertical-align:middle;letter-spacing:.5px}}
.t-b{{background:#2e7d4f}} .t-i{{background:#2563a8}} .t-a{{background:#7b3fb0}}
.t-warn{{background:#b9541b;border-radius:50%;width:13px;height:13px;text-align:center;padding:0;line-height:13px}}
blockquote{{border-left:3px solid {accent};background:{code_bg};margin:3mm 0;padding:2mm 5mm;color:{muted}}}
hr{{border:0;border-top:1px solid {rule};margin:5mm 0}}
ul,ol{{margin:.3em 0 .8em;padding-left:5mm}} li{{margin:.15em 0}} img{{max-width:100%}}
"""

def main():
    ap = argparse.ArgumentParser(description="Build a designed PDF ebook from Markdown.")
    ap.add_argument("files", nargs="*", help="Markdown files in chapter order")
    ap.add_argument("--input-dir", help="Use all *.md in this dir (sorted) instead of listing files")
    ap.add_argument("--output", default="ebook.pdf")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--kicker", default="A FIELD HANDBOOK")
    ap.add_argument("--stats", default="", help="small mono line on the cover, e.g. '23 CHAPTERS · BEGINNER → ADVANCED'")
    ap.add_argument("--cover-image", help="path to a pre-made cover background image (title overlaid via CSS)")
    ap.add_argument("--gen-cover", metavar="IDEA", help="auto-generate the cover background via Gemini "
                    "from this idea (flat, text-free; title overlaid in CSS). Takes precedence over --cover-image.")
    ap.add_argument("--page", choices=["a4", "6x9"], default="a4")
    ap.add_argument("--theme", choices=["light", "dark"], default="light")
    ap.add_argument("--accent", default="#2563eb")
    args = ap.parse_args()

    if args.input_dir:
        input_dir = pathlib.Path(args.input_dir)
        if not input_dir.is_dir():
            sys.exit(f"Input directory not found: {input_dir}")
        paths = sorted(input_dir.glob("*.md"))
    else:
        paths = [pathlib.Path(f) for f in args.files]
    paths = [p for p in paths if p.name.lower() != "readme.md"]
    if not paths:
        sys.exit("No Markdown files given (use files... or --input-dir).")
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        sys.exit("Markdown file(s) not found:\n  " + "\n  ".join(missing))

    md = markdown.Markdown(extensions=["fenced_code","tables","codehilite","attr_list","sane_lists","md_in_html"],
                           extension_configs={"codehilite":{"guess_lang":False}})
    base = pathlib.Path(args.output).resolve().parent
    cover_rel = None
    if args.gen_cover:
        cover_rel = generate_cover(args.gen_cover, base / "cover-generated.png", args.theme)
    if cover_rel is None and args.cover_image:
        cover_rel = pathlib.Path(args.cover_image).resolve()
        if not cover_rel.is_file():
            sys.exit(f"Cover image not found: {cover_rel}")
    css = build_css(args.theme, args.page, args.accent, cover_rel)
    ids = chapter_ids(paths)
    chapters = "".join(render_chapter(md, p, i, ids[p]) for i, p in enumerate(paths, 1))
    today = datetime.date.today().isoformat()
    stats = args.stats or f"{len(paths)} CHAPTERS"
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>
<section class="cover"><div class="scrim-top"></div><div class="scrim-bot"></div>
  <div class="mid"><div class="kick">{html.escape(args.kicker)}</div><div class="bar"></div>
    <h1>{html.escape(args.title)}</h1>
    <div class="sub">{html.escape(args.subtitle)}</div></div>
  <div class="foot"><div class="stats">{html.escape(stats)}</div>{today}</div>
</section>
<nav class="toc"><h1>Table of Contents</h1><hr><ol>{toc(paths, ids)}</ol></nav>
{chapters}</body></html>"""

    out = pathlib.Path(args.output)
    out.with_suffix(".debug.html").write_text(doc, encoding="utf-8")
    HTML(string=doc, base_url=str(base)).write_pdf(str(out))
    print(f"PDF: {out.resolve()}  ({out.stat().st_size//1024} KB, {len(paths)} chapters)")
    print("Tip: visual-validate -> pdftoppm -png -r 150 -f 1 -l 1", out, "prev && open prev-001.png")

if __name__ == "__main__":
    main()
