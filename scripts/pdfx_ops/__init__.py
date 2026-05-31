"""pdfx_ops — modular PDF operations grouped by concern.

Each module exposes cmd_* functions and a register(subparsers) hook so the thin
`pdf_process.py` dispatcher can wire every subcommand without one giant file.
"""
