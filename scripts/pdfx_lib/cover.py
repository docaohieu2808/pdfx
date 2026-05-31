"""AI cover generation via Gemini (Nano Banana) + GEMINI_API_KEY discovery.
Depends only on google-genai; degrades to a CSS gradient cover if unavailable."""
import os, pathlib

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
ENV_CANDIDATES = [
    SKILL_DIR / ".env",
    SKILL_DIR.parent / ".env",
    pathlib.Path.home() / ".agents/.env",
    pathlib.Path.home() / ".claude/.env",
]


def gemini_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    for envfile in ENV_CANDIDATES:
        if envfile.exists():
            for line in envfile.read_text(errors="ignore").splitlines():
                if line.startswith("GEMINI_API_KEY") and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"')
    return None


def generate_cover(idea, out_path, theme):
    """Generate a flat, text-free cover. Returns the saved path or None (fallback)."""
    key = gemini_key()
    if not key:
        print("[gen-cover] no GEMINI_API_KEY (env or .env); using gradient cover.")
        return None
    try:
        from google import genai
        from google.genai import types
    except ModuleNotFoundError:
        print("[gen-cover] google-genai not installed; gradient cover.")
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
