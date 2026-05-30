# Introduction

This chapter validates prose layout, inline `code`, callout badges [B] [I] [A],
and warning markers [!]. The output should look like a published handbook, not a
browser printout.

## Feature checklist

| Feature | Expected result |
|---|---|
| Cover | Full page with title, subtitle, stats, and date |
| TOC | Dot leaders and page numbers |
| Body | Running header, footer page number, readable measure |
| Code | Syntax highlighting and wrapped long lines |

> A short callout should keep enough contrast in both light and dark themes.

## Code sample

```python
def build_pdf(title: str, chapters: list[str]) -> str:
    return f"{title}: {len(chapters)} chapters"
```

