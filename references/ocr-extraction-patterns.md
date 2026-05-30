# OCR and Text Extraction Patterns

## When to Use OCR vs Direct Extraction

**Direct extraction** (pdfplumber, pypdf): PDF has selectable text (created digitally).
**OCR** (pytesseract): PDF is scanned image, no selectable text.

Quick test:
```python
from pypdf import PdfReader
reader = PdfReader("doc.pdf")
text = reader.pages[0].extract_text()
if not text or len(text.strip()) < 10:
    print("Likely scanned — use OCR")
else:
    print("Has extractable text")
```

## OCR Pipeline

### Basic: pytesseract + pdf2image
```python
from pdf2image import convert_from_path
import pytesseract

images = convert_from_path("scanned.pdf", dpi=300)
full_text = []
for i, img in enumerate(images):
    text = pytesseract.image_to_string(img, lang="eng")
    full_text.append(f"--- Page {i+1} ---\n{text}")

result = "\n\n".join(full_text)
```

### Preprocessing for Better OCR

```python
from PIL import Image, ImageFilter, ImageEnhance

def preprocess_for_ocr(img):
    """Improve OCR accuracy with image preprocessing."""
    # Convert to grayscale
    img = img.convert("L")
    # Increase contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    # Binarize (threshold)
    img = img.point(lambda x: 0 if x < 128 else 255)
    # Scale up if small (OCR works better on larger images)
    if img.width < 1000:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return img
```

### OCR with Layout Preservation
```python
# Get word bounding boxes
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
for i in range(len(data["text"])):
    if data["conf"][i] > 60:  # confidence threshold
        word = data["text"][i]
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        print(f"'{word}' at ({x},{y}) size ({w}x{h}) conf={data['conf'][i]}")

# Get structured output (hOCR format)
hocr = pytesseract.image_to_pdf_or_hocr(img, extension="hocr")
```

### Multi-Language OCR
```python
# Install language packs: sudo apt install tesseract-ocr-vie tesseract-ocr-jpn
text = pytesseract.image_to_string(img, lang="eng+vie")  # English + Vietnamese
text = pytesseract.image_to_string(img, lang="jpn")       # Japanese
```

## Table Extraction from Scanned PDFs

### Strategy 1: OCR then Parse
```python
# Extract text with layout, then parse columns
text = pytesseract.image_to_string(img, config="--psm 6")  # Assume uniform text block
lines = text.split("\n")
# Parse fixed-width columns based on character positions
```

### Strategy 2: Use Tabula (for PDFs with text layer)
```bash
pip install tabula-py
```
```python
import tabula
tables = tabula.read_pdf("document.pdf", pages="all", multiple_tables=True)
for df in tables:
    print(df.to_string())
```

### Strategy 3: Detect Table Regions First
```python
import pdfplumber

with pdfplumber.open("doc.pdf") as pdf:
    page = pdf.pages[0]
    # Find table by looking for line intersections
    tables = page.find_tables()
    for table in tables:
        bbox = table.bbox  # (x0, top, x1, bottom)
        extracted = table.extract()
        print(extracted)
```

## Tesseract Configuration

### Page Segmentation Modes (--psm)
| Mode | Description | Use Case |
|------|-------------|----------|
| 3 | Fully automatic (default) | General documents |
| 4 | Single column variable sizes | Articles, reports |
| 6 | Uniform block of text | Tables, forms |
| 7 | Single text line | Headers, labels |
| 8 | Single word | Isolated text fields |
| 11 | Sparse text, no order | Receipts, labels |

### OCR Engine Modes (--oem)
| Mode | Description |
|------|-------------|
| 0 | Legacy engine only |
| 1 | LSTM neural net only (default, best accuracy) |
| 2 | Legacy + LSTM |
| 3 | Default (let Tesseract decide) |

```python
# Custom config
text = pytesseract.image_to_string(img, config="--psm 6 --oem 1 -c preserve_interword_spaces=1")
```

## Batch Processing Pattern

```python
import os, glob
from pdf2image import convert_from_path
import pytesseract

def ocr_directory(input_dir, output_dir, dpi=300, lang="eng"):
    """OCR all PDFs in a directory."""
    os.makedirs(output_dir, exist_ok=True)
    for pdf_path in sorted(glob.glob(f"{input_dir}/*.pdf")):
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"Processing: {name}")
        images = convert_from_path(pdf_path, dpi=dpi)
        text_parts = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang=lang)
            text_parts.append(text)
        output_path = os.path.join(output_dir, f"{name}.txt")
        with open(output_path, "w") as f:
            f.write("\n\n".join(text_parts))
        print(f"  -> {output_path} ({len(images)} pages)")
```

## Quality Assessment

```python
def assess_ocr_quality(text):
    """Quick heuristic check on OCR output quality."""
    words = text.split()
    if not words:
        return {"quality": "empty", "score": 0}
    # Check for common OCR artifacts
    garbage_chars = sum(1 for w in words if len(w) == 1 and not w.isalnum())
    short_gibberish = sum(1 for w in words if len(w) > 1 and not any(c.isalpha() for c in w))
    score = max(0, 100 - (garbage_chars + short_gibberish * 2) / len(words) * 100)
    return {"quality": "good" if score > 80 else "fair" if score > 50 else "poor", "score": round(score)}
```
