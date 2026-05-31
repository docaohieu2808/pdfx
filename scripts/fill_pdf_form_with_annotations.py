import argparse
import json
import pathlib


# Fills a non-fillable PDF by stamping text into entry boxes defined in `fields.json`
# (see forms.md). Text is drawn as real page content with a bundled Unicode TTF font
# (EB Garamond) so Vietnamese diacritics survive and the result is selectable/searchable
# and renders in every viewer — unlike pypdf FreeText annotations, which use a base-14
# WinAnsi font that drops Vietnamese diacritics and rely on viewer-side rendering.

FONT_FILE = pathlib.Path(__file__).resolve().parent.parent / "assets" / "fonts" / "EBGaramond.ttf"


def _hex_color(s):
    s = (s or "000000").lstrip("#")
    return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _entry_rect(bbox, image_width, image_height, pdf_width, pdf_height):
    """image coords [left, top, right, bottom] (origin top-left) -> PDF/fitz rect.
    fitz also uses a top-left origin, so only scale — no Y flip."""
    xs, ys = pdf_width / image_width, pdf_height / image_height
    return [bbox[0] * xs, bbox[1] * ys, bbox[2] * xs, bbox[3] * ys]


def fill_pdf_form(input_pdf_path, fields_json_path, output_pdf_path):
    import fitz  # PyMuPDF

    with open(fields_json_path, "r") as f:
        fields_data = json.load(f)
    doc = fitz.open(input_pdf_path)
    fontfile = str(FONT_FILE) if FONT_FILE.is_file() else None

    stamped = 0
    for field in fields_data["form_fields"]:
        entry = field.get("entry_text") or {}
        text = entry.get("text")
        if not text:
            continue
        page_num = field["page_number"]
        page = doc[page_num - 1]
        info = next(p for p in fields_data["pages"] if p["page_number"] == page_num)
        rect = _entry_rect(field["entry_bounding_box"], info["image_width"],
                           info["image_height"], page.rect.width, page.rect.height)
        size = float(entry.get("font_size", 14))
        color = _hex_color(entry.get("font_color"))
        # Try to fit the text in the box, shrinking if needed (insert_textbox returns
        # a negative remainder when it overflows).
        for fs in (size, size * 0.85, size * 0.7):
            rc = page.insert_textbox(fitz.Rect(*rect), text, fontsize=fs, color=color,
                                     fontname="vnfont", fontfile=fontfile, align=0)
            if rc >= 0:
                break
        stamped += 1

    doc.save(output_pdf_path, garbage=3, deflate=True)
    print(f"Successfully filled PDF form and saved to {output_pdf_path}")
    print(f"Stamped {stamped} text field(s) with a Unicode font (Vietnamese-safe)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill a PDF form with text annotations from fields.json.")
    parser.add_argument("input_pdf", help="Input PDF file")
    parser.add_argument("fields_json", help="fields.json with form data (see forms.md)")
    parser.add_argument("output_pdf", help="Output PDF file")
    args = parser.parse_args()
    fill_pdf_form(args.input_pdf, args.fields_json, args.output_pdf)
