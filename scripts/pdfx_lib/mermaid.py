"""Render ```mermaid fenced code blocks to SVG (best-effort).

Tries `mmdc` (mermaid-cli) on PATH, then `npx @mermaid-js/mermaid-cli`. Both need
a headless Chromium; if neither works the caller keeps the block as a styled code
listing so the build always succeeds. WeasyPrint then embeds the produced SVG via
<img>, which renders crisply (unlike inline SVG, it bypasses md_in_html)."""
import re, shutil, subprocess, tempfile, json, pathlib

FENCE = re.compile(r'^```mermaid[ \t]*\n(.*?)\n```[ \t]*$', re.DOTALL | re.MULTILINE)


def _renderer():
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        return ["npx", "-y", "@mermaid-js/mermaid-cli"]
    return None


def _render_one(src, out_svg, pcfg, mcfg):
    base = _renderer()
    if not base:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as fh:
        fh.write(src)
        mmd = fh.name
    # -c mermaid config forces htmlLabels:false so labels become real SVG <text>
    # (WeasyPrint cannot render the default <foreignObject> HTML labels).
    cmd = base + ["-i", mmd, "-o", str(out_svg), "-b", "transparent", "-p", pcfg, "-c", mcfg]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=240)
        return out_svg.exists()
    except Exception:
        return False
    finally:
        pathlib.Path(mmd).unlink(missing_ok=True)


def expand(md_text, assets_dir, stem):
    """Replace mermaid fences with <img> to rendered SVGs. Returns (text, rendered_count).
    Unrenderable blocks fall back to a labelled code listing."""
    blocks = FENCE.findall(md_text)
    if not blocks:
        return md_text, 0
    assets_dir = pathlib.Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    pcfg = assets_dir / "_puppeteer.json"
    pcfg.write_text(json.dumps({"args": ["--no-sandbox", "--disable-gpu"]}))
    mcfg = assets_dir / "_mermaid.json"
    mcfg.write_text(json.dumps({"htmlLabels": False, "flowchart": {"htmlLabels": False},
                                "themeVariables": {"fontFamily": "sans-serif"}}))
    rendered = {"n": 0, "i": 0}

    def repl(m):
        src = m.group(1)
        out_svg = assets_dir / f"{stem}-mermaid-{rendered['i']}.svg"
        rendered["i"] += 1
        if _render_one(src, out_svg, str(pcfg), str(mcfg)):
            rendered["n"] += 1
            return f'\n\n<img src="{out_svg.as_posix()}" alt="mermaid diagram" style="width:100%">\n\n'
        # fallback: keep the source visible so nothing is lost
        return f'\n\n> ⚠ mermaid (renderer unavailable — showing source)\n\n```\n{src}\n```\n\n'

    return FENCE.sub(repl, md_text), rendered["n"]
