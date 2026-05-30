# PDF Manipulation Guide

## Library Selection

| Task | Best Library | Notes |
|------|-------------|-------|
| Read/merge/split/rotate | pypdf | Pure Python, no deps |
| Text extraction (layout) | pdfplumber | Preserves spatial layout |
| Table extraction | pdfplumber | Best table detection |
| Create from scratch | reportlab | Full layout control |
| Fill forms | pypdf or pdf-lib (JS) | See forms.md |
| OCR scanned PDFs | pytesseract + pdf2image | Needs Tesseract installed |
| Command-line ops | qpdf, pdftotext, pdftk | Fast, scriptable |
| Metadata editing | pypdf | Read/write PDF metadata |
| Watermarking | pypdf (merge_page) | Overlay technique |
| Encryption/decryption | pypdf or qpdf | User + owner passwords |

## pypdf Patterns

### Selective Page Extraction
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

# Extract pages 2-5 (0-indexed)
for i in range(1, 5):
    writer.add_page(reader.pages[i])

# Extract even pages only
for i in range(0, len(reader.pages), 2):
    writer.add_page(reader.pages[i])

with open("output.pdf", "wb") as f:
    writer.write(f)
```

### Page Transformations
```python
# Scale page
page = reader.pages[0]
page.scale_by(0.5)  # 50% size

# Crop page (in points, 1 inch = 72 points)
page.mediabox.lower_left = (72, 72)
page.mediabox.upper_right = (540, 720)

# Merge pages (overlay)
background = PdfReader("bg.pdf").pages[0]
foreground = PdfReader("fg.pdf").pages[0]
background.merge_page(foreground)
```

### Metadata Operations
```python
# Read
meta = reader.metadata
info = {
    "title": meta.title,
    "author": meta.author,
    "subject": meta.subject,
    "creator": meta.creator,
    "producer": meta.producer,
    "pages": len(reader.pages),
}

# Write
writer.add_metadata({
    "/Title": "New Title",
    "/Author": "Author Name",
    "/Subject": "Document Subject",
    "/Keywords": "keyword1, keyword2",
})
```

## pdfplumber Advanced Extraction

### Targeted Text Extraction
```python
import pdfplumber

with pdfplumber.open("doc.pdf") as pdf:
    page = pdf.pages[0]

    # Extract from specific region (x0, top, x1, bottom)
    bbox = (50, 100, 400, 300)
    cropped = page.crop(bbox)
    text = cropped.extract_text()

    # Get word-level positions
    words = page.extract_words()
    for w in words:
        print(f"'{w['text']}' at ({w['x0']:.0f}, {w['top']:.0f})")
```

### Table Extraction with Custom Settings
```python
table_settings = {
    "vertical_strategy": "lines",    # or "text", "explicit"
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "edge_min_length": 3,
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
}
tables = page.extract_tables(table_settings)
```

## reportlab Document Creation

### Table in PDF
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

doc = SimpleDocTemplate("table.pdf", pagesize=letter)
data = [
    ["Name", "Age", "City"],
    ["Alice", "30", "NYC"],
    ["Bob", "25", "LA"],
]
table = Table(data)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
]))
doc.build([table])
```

## Command-Line Quick Reference

```bash
# Page count
qpdf --show-npages input.pdf

# Extract text (preserve layout)
pdftotext -layout input.pdf output.txt

# Merge with page ranges
qpdf --empty --pages a.pdf 1-3 b.pdf 5-10 -- merged.pdf

# Compress/optimize
qpdf --linearize --compress-streams=y input.pdf optimized.pdf

# Remove password
qpdf --password=secret --decrypt encrypted.pdf decrypted.pdf

# Repair corrupted PDF
qpdf --replace-input damaged.pdf

# Extract images
pdfimages -j input.pdf output_prefix
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Blank text extraction | PDF is scanned image — use OCR (pytesseract) |
| Garbled text | Font encoding issue — try pdftotext or pdfplumber |
| Table extraction fails | Adjust `vertical_strategy`/`horizontal_strategy` in pdfplumber |
| Large file size | Compress images, use qpdf `--compress-streams` |
| Password protected | Use `qpdf --decrypt` or `reader = PdfReader("f.pdf", password="pw")` |
| Merge loses bookmarks | Use `writer.add_outline_item()` to recreate |
