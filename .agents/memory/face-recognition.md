---
name: Face recognition system architecture
description: How the face attendance system in attendance.py works — key design decisions
---

# Face Recognition System

## Key decisions

- **No manual enrollment step** — `_auto_generate_encodings(gym_id)` runs on every face tab load; silently generates face encodings from profile photos already in Object Storage for members who have photo but no `face_encoding` column.
- **Always-on auto mode** — `_AUTO_CLICK_JS` is always injected (no staff toggle); auto-clicks camera input every 5 seconds; uses `window._gymFaceTick` guard to prevent duplicate intervals.
- **Camera key** — `key=f"fac_{int(time.time()//8)}"` forces a fresh capture cycle every 8 seconds without user action.
- **Unknown/expired captures** — saved to Object Storage under `unknown_captures/{gym_id}/{ts}_{type}.jpg` AND recorded in `UnknownCapture` DB table. `_save_capture()` compresses to 240×180 JPEG at q=55 before upload.
- **3-day auto-delete** — `_run_cleanup()` called on every face tab load; calls `db.cleanup_old_captures(days=3)` which returns keys, then `object_store.delete_capture(key)` for each.
- **CPU efficiency** — resize frame to max 320px wide before face processing; 5-second interval between captures.
- **Encoding cache** — TTL = 300 seconds per gym_id in session state (`face_enc_cache`, `face_enc_cache_ts`, `face_enc_cache_gym`).
- **Admin capture panel** — only visible for `role in ("admin","auditor")`; shows captured image from Object Storage, timestamp, type badge; per-item delete + bulk delete.

**Why:** user requirement — staff can't accidentally disable face detection; profile photos already on file eliminate manual enrollment friction; unknown captures only (not video) keeps storage minimal.

## Files changed
- `gym-app/database.py` — `UnknownCapture` ORM model + `add_unknown_capture`, `get_unknown_captures`, `delete_unknown_capture_record`, `cleanup_old_captures` CRUD; `init_db` creates the table.
- `gym-app/gym_pages/attendance.py` — complete rewrite of face section (lines ~486–880): `_face_ss_init`, `_load_encodings`, `_auto_generate_encodings`, `_run_cleanup`, `_save_capture`, `_match_face`, `_result_banner`, `_process_face_image`, `render_face_recognition_tab`, `_safe_date`.
- `gym-app/object_store.py` — `upload_capture`, `get_capture_bytes`, `delete_capture` (added in prior session).
- `gym-app/face_engine.py` — OpenCV Haar Cascade + cosine similarity core (added in prior session).
