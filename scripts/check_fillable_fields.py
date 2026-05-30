import argparse


# Script for Claude to run to determine whether a PDF has fillable form fields. See forms.md.


def check_fillable(pdf_path: str) -> None:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    if reader.get_fields():
        print("This PDF has fillable form fields")
    else:
        print("This PDF does not have fillable form fields; you will need to visually determine where to enter data")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if a PDF has fillable form fields.")
    parser.add_argument("pdf_path", help="Input PDF file to check")
    args = parser.parse_args()
    check_fillable(args.pdf_path)
