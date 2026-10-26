"""Table of contents (depth-aware, with part headers), A-Z back-of-book index,
and full-page part-divider sections."""
import re, html, unicodedata

ROW_TERM = re.compile(r'^\s*\|\s*\*\*(.+?)\*\*\s*\|', re.MULTILINE)  # bold first table cell
INLINE_TERM = re.compile(r'\[\[(.+?)\]\]')  # explicit [[term]] marker


def part_divider_html(title, idx):
    return (f'<section class="part-divider" id="part-{idx}">'
            f'<div class="part-kicker">PHẦN</div>'
            f'<h1 class="part-title">{html.escape(title)}</h1></section>')


def build_toc(chapters, parts, toc_depth):
    """chapters: [(num, title, cid, subheadings)]; parts: {num: part_title}."""
    rows = []
    for num, title, cid, subs in chapters:
        if num in parts:
            rows.append(f'<li class="toc-part">{html.escape(parts[num])}</li>')
        rows.append(f'<li><a href="#ch-{cid}"><span class="tnum">{num:02d}</span>'
                    f'<span class="tttl">{html.escape(title)}</span></a></li>')
        if toc_depth >= 2:
            for text, hid in subs:
                rows.append(f'<li class="toc-sub"><a href="#{hid}">'
                            f'<span class="tttl">{html.escape(text)}</span></a></li>')
    return "\n".join(rows)


def extract_terms(raw_md):
    """Index terms = bold first table cell (**term**) + explicit [[term]] markers."""
    terms = set()
    for m in ROW_TERM.finditer(raw_md):
        terms.add(m.group(1).strip())
    for m in INLINE_TERM.finditer(raw_md):
        terms.add(m.group(1).strip())
    return terms


def _slug(t):
    return re.sub(r"[^a-z0-9]+", "-", _sortkey(t)).strip("-") or str(abs(hash(t)))


def anchor_terms(section_html, terms, chapter):
    """Give the first occurrence of each index term in a chapter an id, so the index can print the page it is on.
    A [[term]] marker wins over a bold table cell; every marker is then shown as plain text.
    Returns (html, {term: anchor_id})."""
    found = {}
    for t in sorted(terms, key=_sortkey):
        aid = f"ix-{chapter}-{_slug(t)}"
        esc = html.escape(t, quote=False)
        marker, bold = f"[[{esc}]]", f"<strong>{esc}</strong>"
        if marker in section_html:
            section_html = section_html.replace(marker, f'<span id="{aid}">{esc}</span>', 1)
        elif bold in section_html:
            section_html = section_html.replace(bold, f'<strong id="{aid}">{esc}</strong>', 1)
        else:
            continue
        found[t] = aid
    return strip_markers(section_html), found


def strip_markers(section_html):
    """[[term]] only marks a term for the index; the reader sees the term itself."""
    return INLINE_TERM.sub(lambda m: m.group(1), section_html)


def _sortkey(t):
    ascii_ = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return ascii_ or t.lower()


def build_index(term_map):
    """term_map: {term: [anchor ids]} -> A-Z grouped HTML index section; each anchor prints its page number."""
    if not term_map:
        return ""
    groups = {}
    for term in sorted(term_map, key=_sortkey):
        letter = (_sortkey(term)[:1] or "#").upper()
        if not letter.isalpha():
            letter = "#"
        groups.setdefault(letter, []).append(term)
    blocks = []
    for letter in sorted(groups):
        items = "".join(
            f'<li>{html.escape(t)} <span class="ix-ref">'
            f'{", ".join(f'<a href="#{a}"></a>' for a in term_map[t])}</span></li>'
            for t in groups[letter])
        blocks.append(f'<h3 class="ix-letter">{letter}</h3><ul class="ix-list">{items}</ul>')
    return ('<section class="index-page" id="index"><h1 class="ix-title">Index</h1>'
            + "".join(blocks) + "</section>")
