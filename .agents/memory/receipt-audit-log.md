---
name: Receipt audit log
description: receipt_logs table structure, log_receipt(), update_print_issued(), get_receipt_logs()
---

# Receipt Audit Log

Table: `receipt_logs` in database.py (ReceiptLog SQLAlchemy model).

**Rule:** After every successful `add_fee_record()`, call `db.log_receipt(...)` with `print_issued=False`. If thermal print succeeds, call `db.update_print_issued(receipt_no, True)`.

**Why:** Audit trail showing which receipts were physically printed vs. only recorded digitally.

**How to apply:**
- `receipt_no` is extracted from `add_fee_record()` return msg: `msg.split("Receipt: ")[-1].strip()`
- Admin-only reprint tab in fee_collection.py (3rd tab only shown to role='admin')
- `db.get_receipt_logs(gym_id)` returns list of dicts for the audit table
