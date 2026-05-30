import argparse
import os
import sys


# Converts each page of a PDF to a PNG image.


def convert(pdf_path, output_dir, max_dim=1000):
    from pdf2image import convert_from_path

    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=200)

    for i, image in enumerate(images):
        # Scale image if needed to keep width/height under `max_dim`
        width, height = image.size
        if width > max_dim or height > max_dim:
            scale_factor = min(max_dim / width, max_dim / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height))
        
        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path)
        print(f"Saved page {i+1} as {image_path} (size: {image.size})")

    print(f"Converted {len(images)} pages to PNG images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert each PDF page to a PNG image.")
    parser.add_argument("pdf_path", help="Input PDF file")
    parser.add_argument("output_dir", help="Output directory for PNG images")
    parser.add_argument("--max-dim", type=int, default=1000, help="Max image dimension (default: 1000)")
    args = parser.parse_args()

    try:
        from pdf2image import convert_from_path  # noqa: F401
    except ImportError:
        print("Error: pdf2image not installed. Run: pip install pdf2image", file=sys.stderr)
        sys.exit(1)

    convert(args.pdf_path, args.output_dir, args.max_dim)
