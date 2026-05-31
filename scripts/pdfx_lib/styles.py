"""Print CSS for the ebook: cover, TOC (with parts + sub-entries), chapters,
code, tables, part dividers, and the A-Z index."""
import pathlib
from pygments.formatters import HtmlFormatter

FONTS = pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"


def build_css(theme, page, accent, cover_image):
    size = "A4" if page == "a4" else "6in 9in"
    cover_height = "297mm" if page == "a4" else "9in"
    body_pt = "10pt" if page == "a4" else "11pt"
    dark = theme == "dark"
    ink = "#e8eef5" if dark else "#1f2430"
    bg = "#10151c" if dark else "#ffffff"
    muted = "#9aa6b4" if dark else "#5c6470"
    rule = "#2a313c" if dark else "#d9dee6"
    code_bg = "#161c24" if dark else "#f6f8fa"
    cover_base = "#0f1722" if dark else "#f4f7fb"
    pyg = HtmlFormatter(style="dracula" if dark else "friendly").get_style_defs(".codehilite")
    if cover_image:
        cover_bg = f"{cover_base} url({cover_image}) center top/cover no-repeat"
    elif dark:
        cover_bg = "radial-gradient(130% 80% at 50% -15%,#1d3a52 0%,#0f2233 55%,#081523 100%)"
    else:
        cover_bg = "linear-gradient(160deg,#ffffff 0%,#eaf1fb 60%,#dce8f7 100%)"
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
nav.toc .toc-part{{font-family:'Inter';font-weight:700;font-size:9pt;letter-spacing:2px;
  text-transform:uppercase;color:{accent};margin:6mm 0 2.5mm}}
nav.toc .toc-sub{{margin:0 0 2mm 9mm}} nav.toc .toc-sub a{{font-size:9.5pt;color:{muted}}}

.part-divider{{page:nohead;break-before:page;height:230mm;display:flex;flex-direction:column;
  justify-content:center;align-items:center;text-align:center}}
.part-divider .part-kicker{{font-family:'JetBrains Mono';letter-spacing:6px;font-size:11pt;color:{accent}}}
.part-divider .part-title{{font-family:'Display';font-size:34pt;font-weight:800;margin:6mm 0 0;
  border-top:2px solid {accent};border-bottom:2px solid {accent};padding:5mm 0;bookmark-level:1;bookmark-label:content()}}

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

.index-page{{break-before:page;columns:2;column-gap:10mm}}
.index-page .ix-title{{font-family:'Display';font-size:27pt;margin:0 0 4mm;column-span:all;
  border-bottom:2px solid {accent};padding-bottom:3mm;bookmark-level:1;bookmark-label:'Index'}}
.ix-letter{{font-family:'Inter';font-weight:800;font-size:12pt;color:{accent};margin:3mm 0 1mm;break-after:avoid}}
.ix-list{{list-style:none;margin:0 0 3mm;padding:0;font-size:9pt}} .ix-list li{{margin:.6mm 0}}
.ix-ref{{color:{muted};font-family:'JetBrains Mono';font-size:8pt;float:right}}
"""
