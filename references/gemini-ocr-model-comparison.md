# Research: Which Gemini vision model is best for OCR

_Conducted 2026-05-31 · for pdfx `ocr --engine gemini` · empirical (live API key) + web._

## TL;DR
- **Best default → `gemini-2.5-flash`** (GA, not "preview", fast ~1.8s, accurate, cheap $0.30/1M in). This is what pdfx defaults to.
- **Highest accuracy on hard scans → `gemini-3.5-flash`** (or `gemini-3-flash-preview`) — **#1 on OCR Arena** (ELO 1750, beats 2.5-flash 57.9%). ~2× slower (~3.8–7.5s).
- **Cheapest / bulk → `gemini-2.5-flash-lite`** ($0.10/1M, batch $0.05) — but **lite drops words** on noisy scans (test: lost "Thiên Huế"; forum reports a 3.1-flash-lite regression). Do not make it the default.
- **Pro tier is NOT worth it for OCR** (see below): slower and no accuracy gain. OCR is a perception task, not a reasoning task.
- **Avoid** `gemini-2.0-flash*` — deprecated, shut down 2026-06-01.

## Empirical (same Vietnamese-with-diacritics images)
### Clean text
| Model | Latency | Accuracy (sim) |
|---|---|---|
| gemini-2.5-flash-lite | 1.6s | 0.983 |
| gemini-2.5-flash | 2.2s | 0.983 |
| gemini-2.5-pro | 5.9s | 0.992 |
| flash-latest / pro-latest | 7.0–7.7s | 1.000 |

### Simulated scan (small font, noise, blur, 1.4° skew) — more representative
| Model | Latency | Accuracy | Note |
|---|---|---|---|
| gemini-2.5-flash-lite | 2.9s | 0.973 | **dropped "Thiên Huế"** |
| **gemini-2.5-flash** | **1.8s** | **1.000** | fast + correct ✅ |
| gemini-3-flash-preview | 3.8s | 0.992 | turned `—` into `--` |
| **gemini-3.5-flash** | 3.8s | **1.000** | newest, correct |
| **gemini-3.1-flash-lite** | **1.6s** | **1.000** | fastest, correct (but lite = risk on hard docs) |

→ On clean / lightly-degraded text every flash model is ~perfect (saturates). Real differences only appear on **badly** degraded documents (below).

## Pro tier (tested 2026-05-31, HARD scan: small font + blur + noise + skew + low-contrast gray)
| Model | Latency | Accuracy | Note |
|---|---|---|---|
| gemini-2.5-flash | 4.6s | 0.963 | |
| **gemini-3.5-flash** | 7.5s | **0.974** | winner |
| gemini-2.5-pro | 5.8s | 0.963 | over-corrected ("Khuỷu"→"Khả") |
| gemini-3-pro-preview | — | — | **404 "no longer available"** (retired alias) |
| gemini-3.1-pro-preview | **71s** | 0.963 | absurdly slow, no gain |

**→ Pro is NOT worth it for OCR.** OCR is perception, not reasoning, so a pro model's extra
"thinking" only adds latency and sometimes over-corrects. **flash ≥ pro for OCR.** Note: there is no
`gemini-3.0-pro`; `gemini-3-pro-preview` has been pulled. A future "3.5-pro" is unlikely to beat
3.5-flash for OCR for the same reason — re-test when it ships.

## Web cross-check
- [OCR Arena: Gemini 3 Flash #1 (ELO 1750) vs 2.5 Flash #7 (1634)](https://www.ocrarena.ai/compare/gemini-2-5-pro/gemini-3-flash)
- [Forum: OCR regression 2.5-flash → 3.1-flash-lite](https://discuss.ai.google.dev/t/critical-ocr-performance-regression-2-5-flash-vs-3-1-flash-lite/145361) — lite is not always better.
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing): 2.5-flash $0.30/$2.50; 2.5-flash-lite $0.10/$0.40 (batch −50%). 2.0-flash deprecated 2026-06-01.
- [Large-PDF OCR with 2.5-flash methodology](https://medium.com/@xavierjesudhas3/conquering-large-pdf-ocr-with-gemini-2-5-flash-a-streamlined-methodology-babfa172f665)

## Recommendation for pdfx
1. Keep default `gemini-2.5-flash` (GA, stable, won't be removed like a preview).
2. Docs note: `--model gemini-3.5-flash` for the hardest scans; `--model gemini-2.5-flash-lite` for cheap bulk (accept occasional dropped words).
3. Do not use pro / 2.0 / lite as the default.

## Unresolved
- Not yet tested on **phone photos / real paper scans** (creases, shadows, handwriting). Re-test with a real file.
- Even 3.5-flash still misses rare syllables (Nghiễm→Nghiêm, Khuỷu→Khuyến) on trashy images → human review needed for critical Vietnamese.
