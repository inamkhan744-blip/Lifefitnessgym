---
name: Anti-theft activity log
description: ActivityLog model and staff monitoring system added to GymPro for anti-theft fee tracking
---

## What was built

- **`ActivityLog` model** added to `database.py` (after `AppSetting` class) — columns: id, gym_id, user, role, action, details, amount, record_ref, created_at. Has `back_populates="activity_logs"` on `Gym` model.
- **`log_activity(user, action, details, gym_id, role, amount, record_ref)`** — safe fire-and-forget logger (never raises).
- **`get_activity_logs(gym_id, limit, date_from, date_to, user, action)`** — filtered query, newest first.
- **`get_daily_fee_summary(gym_id, target_date)`** — returns (total, count, records) for cash reconciliation.

## Logging call sites in fee_collection.py

- `FEE_COLLECTED` — after `db.add_fee_record` succeeds, before receipt generation.
- `FEE_EDITED` — after `db.update_fee_record` succeeds.
- `FEE_DELETED` — after `db.delete_fee_record` succeeds.
- `render_history_admin(gym_id, role, current_user="")` — accepts current_user so logs know who acted.

## Staff Monitor tab (auditor.py)

- 6th tab: `"🛡️ Staff Monitor"` added to `tab_staff`.
- **Cash Reconciliation**: shows today's total, receipt count, per-staff breakdown table.
- **Activity Log**: colour-coded table (green=collected, yellow=edited, red=deleted); filterable by date, staff name, action type; CSV download.

**Why:** Staff were collecting fees without issuing receipts and pocketing cash — no audit trail existed. This system makes every fee action visible to the admin in real time.
