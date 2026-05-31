"""Chapter rendering: badges, slugs, chapter ids, inline-SVG protection,
mermaid expansion, heading-id injection (for depth-2 TOC), render_chapter."""
import re, html as _html
from . import mermaid

TAG = re.compile(r'\[(B|I|A)\]')
GOTCHA = re.compile(r'\[!\]')
SVG_RE = re.compile(r'<svg\b.*?</svg>', re.DOTALL | re.IGNORECASE)
H2_RE = re.compile(r'<h2([^>]*)>(.*?)</h2>', re.DOTALL)


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
    seen, ids = {}, {}
    for path in paths:
        base = slugify(path.stem, f"chapter-{len(ids) + 1}")
        count = seen.get(base, 0) + 1
        seen[base] = count
        ids[path] = base if count == 1 else f"{base}-{count}"
    return ids


def _protect_svg(text):
    """Stash inline <svg> blocks behind tokens so md_in_html can't mangle them."""
    store = []

    def stash(m):
        store.append(m.group(0))
        return f"\n\nxPDFXSVG{len(store) - 1}Xx\n\n"
    return SVG_RE.sub(stash, text), store


def _restore_svg(html_text, store):
    for i, svg in enumerate(store):
        html_text = re.sub(rf'(<p>\s*)?xPDFXSVG{i}Xx(\s*</p>)?',
                           lambda m, s=svg: s, html_text)
    return html_text


def _add_h2_ids(html_text, chapter_id, collect):
    """Give every <h2> a chapter-scoped id and record it for the TOC (doc order)."""
    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub("<[^>]+>", "", inner).strip()
        hid = f"{chapter_id}--{slugify(text, 'h')}-{len(collect)}"
        collect.append((text, hid))
        idattr = "" if "id=" in attrs else f' id="{hid}"'
        return f"<h2{attrs}{idattr}>{inner}</h2>"
    return H2_RE.sub(repl, html_text)


def render_chapter(md, path, num, chapter_id, assets_dir, toc_depth=1):
    """Return (section_html, title, sub_headings). sub_headings=[(text,id),...] when depth>=2."""
    raw = path.read_text(encoding="utf-8")
    title = first_h1(raw, path.stem)
    body_md = re.sub(r'^# .*\n?', '', raw, count=1, flags=re.MULTILINE)
    body_md, _ = mermaid.expand(body_md, assets_dir, chapter_id)
    body_md, svg_store = _protect_svg(body_md)
    md.reset()
    body = _restore_svg(md.convert(body_md), svg_store)
    body = badges(body)
    headings = []
    if toc_depth >= 2:
        body = _add_h2_ids(body, chapter_id, headings)
    section = (f'<section class="chapter" id="ch-{chapter_id}">\n'
               f'  <header class="chap-head"><div class="chap-num">{num:02d}</div>\n'
               f'  <h1 class="chap-title">{_html.escape(title)}</h1></header>\n  {body}\n</section>')
    return section, title, headings
