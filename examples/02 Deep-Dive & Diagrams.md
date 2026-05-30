# Deep Dive & Diagrams

This chapter validates sanitized chapter anchors from a filename with spaces and
symbols. It also checks long shell lines and ASCII diagram alignment.

## Long command

```bash
python scripts/build_ebook_from_markdown.py --title "Very Long Technical Handbook Title" --subtitle "A Practical Reference" --page a4 --theme light --accent "#2563eb" --output handbook.pdf chapters/01-intro.md chapters/02-architecture.md chapters/03-operations.md
```

## ASCII diagram

```text
Markdown files
     |
     v
HTML + CSS print rules
     |
     v
WeasyPrint renderer
     |
     v
Publication-quality PDF
```

