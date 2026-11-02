---
name: Thermal printer refactor
description: How the 80mm thermal printer module is structured and integrated in fee_collection.py
---

# Thermal Printer Module

The old `ReceiptPrinter` class in `fee_collection.py` was replaced with `gym-app/printer_utils.py`.

**Rule:** fee_collection.py imports `format_receipt, print_single, print_dual, render_print_preview, check_printer` from `printer_utils`.
- `print_single(data)` → returns `(bool, message)` tuple
- `print_dual(data)` → returns `(bool, message)` tuple
- `check_printer()` → returns `(bool, message)` tuple
- `render_print_preview(data, copies)` — renders 80mm text preview in Streamlit

**Why:** Clean separation; printer_utils.py is 32-char width, no emojis, Linux `lp` command, all wrapped in try-except.

**How to apply:** Any new page that needs thermal printing should import from printer_utils, not re-implement the class.
