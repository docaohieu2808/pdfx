# WeasyPrint Recipes — beautiful PDF/ebook CSS

Copy-paste print-CSS patterns that make a PDF look published. Tested on WeasyPrint 68.
All of these are print-CSS features a headless browser (Chromium `--print-to-pdf`) does
NOT support well — which is why WeasyPrint is the engine for this skill.

## Page setup, running header & footer
```css
@page {
  size: A4;                 /* or "6in 9in" for prose; A4 for code/table-heavy books */
  margin: 20mm 18mm 18mm;
  @top-center    { content: string(doctitle); font-size: 7pt; color: #888; }  /* per-chapter */
  @bottom-center { content: counter(page);     font-size: 9pt; color: #888; }
}
@page cover  { margin: 0; @top-center { content: none } @bottom-center { content: none } }
@page nohead { @top-center { content: none } }     /* assign via  selector { page: nohead } */
```
Per-chapter running header: set a named string on the chapter title, read it in `@top-center`:
```css
.chap-title { string-set: doctitle content(); }
```

## Table of Contents with auto page numbers + dot leaders
The single most "published-looking" feature. Requires `target-counter` (WeasyPrint/Prince
only — Chromium can't do it).
```css
nav.toc a            { display: block; }     /* MUST be block — flex makes leader() collapse */
nav.toc a::after     { content: leader('. ') target-counter(attr(href), page); }
```
```html
<nav class="toc"><ol>
  <li><a href="#ch-intro">Introduction</a></li>
  <li><a href="#ch-setup">Setup</a></li>
</ol></nav>
...
<section id="ch-intro"><h1>Introduction</h1>...</section>
```
`leader('. ')` fills the line with dots; `target-counter(attr(href), page)` prints the
resolved page number of the linked anchor.

## PDF bookmarks (clickable outline panel)
```css
h1 { bookmark-level: 1; bookmark-label: content(); }
h2 { bookmark-level: 2; bookmark-label: content(); }
```

## Code blocks — highlight + no overflow
python-markdown `codehilite` emits `<div class="codehilite"><pre>…pygments spans…</pre></div>`.
Get the theme CSS once: `HtmlFormatter(style="friendly").get_style_defs(".codehilite")`.
```css
.codehilite      { background:#f6f8fa; border:1px solid #e3e8ee; border-radius:5px;
                   padding:5px 9px; font-size:8.2pt; line-height:1.42; }
.codehilite pre  { margin:0; white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word; }
code, pre        { font-family:'JetBrains Mono','DejaVu Sans Mono',monospace; }
```
- `pre-wrap` + `overflow-wrap:anywhere` wraps 200-char shell one-liners instead of clipping.
- A mono font with **box-drawing glyphs** (JetBrains Mono, DejaVu Sans Mono) keeps ASCII
  architecture diagrams aligned. Narrow diagrams (<~90 chars at 8pt on A4) won't wrap.

## Drop cap — span-based (avoid a WeasyPrint bug)
```css
.lead .dropcap { font-family:'Display'; font-weight:800; float:left; font-size:52pt;
                 line-height:.72; padding:1mm 3mm 0 0; color:#8a5a2b; }
```
```html
<p class="lead"><span class="dropcap">G</span>ood design begins with emptiness…</p>
```
Do **NOT** use `p::first-letter { float:left }` — WeasyPrint raises
`AssertionError: isinstance(box, boxes.BlockReplacedBox)` on a floated `::first-letter`.

## Cover with a full-bleed image + crisp overlaid title
AI/photo covers garble baked-in text — generate the image WITHOUT text and overlay the
title in CSS. A scrim gradient keeps text legible on busy/light/dark art.
```css
.cover            { page:cover; height:297mm; position:relative; color:#13233a;
                    background:#f4f7fb url(cover.png) center top/cover no-repeat; }
.cover .scrim-top { position:absolute; top:0; left:0; right:0; height:160mm;
                    background:linear-gradient(180deg,
                      rgba(244,247,251,.99) 0%, rgba(244,247,251,.95) 40%,
                      rgba(244,247,251,.6) 66%, rgba(244,247,251,0) 100%); }
.cover .mid       { position:absolute; left:18mm; right:18mm; top:32mm; text-align:center; }
```
Source order: put `.scrim-*` before the title block so the title paints on top of the scrim,
which paints on top of the background image. Tune scrim height/opacity by eye in the
validation loop (light image → light scrim rgba; dark image → dark scrim + light text).
Use `height:297mm` for A4 covers and `height:9in` for 6x9 covers; a mismatched height can
push footer stats/date off-page.

## Fonts
```css
@font-face { font-family:'Display'; src:url(assets/fonts/PlayfairDisplay.ttf); font-weight:400 900; }
```
Paths resolve against WeasyPrint's `base_url` (pass `HTML(string=doc, base_url=DIR)`).
Variable fonts work via a `font-weight` range.

## Page-size guidance
| Content | Page | Why |
|---------|------|-----|
| Prose / essay / narrative | `6in 9in` | Held-book feel, short measure |
| Technical (code, tables, diagrams) | `A4` | Wider — fewer code wraps, tables fit |

## Gotcha checklist (all hit during real builds)
- TOC numbers missing → `<a>` was `display:flex`; make it `block`.
- Long code line clipped at page edge → add `white-space:pre-wrap; overflow-wrap:anywhere`.
- Crash on drop cap → using `::first-letter{float}`; switch to a `<span>`.
- Cover title unreadable on image → add a scrim gradient; never put dark text on a dark image.
- Box-drawing diagram misaligned → non-mono font, or `pre-wrap` wrapped a too-wide diagram
  (shrink font or use A4).
- Bookmarks missing → set `bookmark-level` (WeasyPrint does not auto-bookmark every build).
- Always run the visual-validation loop before declaring done.
