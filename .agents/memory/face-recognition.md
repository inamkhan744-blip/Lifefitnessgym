---
name: Face recognition system architecture
description: How the face attendance system in attendance.py works — key design decisions and hard-won fixes
---

# Face Recognition System

## CRITICAL: Camera capture loop — stable-key pattern

**Time-rotating camera key + `run_every` = total failure.** Both fire on the same tick; the captured photo is discarded before it arrives.

**Correct pattern (as of current code):**
```python
@st.fragment   # NO run_every — JS click triggers fragment reruns
def _face_camera_fragment(...):
    cam_gen = st.session_state.face_cam_gen  # stable int, starts at 0
    cam_img = st.camera_input("Camera", key=f"fac_{cam_gen}", ...)
    if cam_img is not None:
        result = _process_face_image(...)
        st.session_state.face_cam_gen += 1   # advance AFTER processing
        st.rerun(scope="fragment")           # reset camera for next shot
```

JS auto-click (every 5 s) → "Take Photo" → widget change → fragment reruns → photo arrives → process → increment gen → camera resets → repeat.

**Why `run_every` removed:** server-side reruns are independent of widget events. If the key also rotates on a timer, both reset simultaneously and captured frame is lost. Without `run_every`, only widget changes trigger the fragment — clean reliable loop.

## Similarity threshold — must be 0.40

`SIMILARITY_THRESHOLD = 0.40` in `face_engine.py` and `FACE_THRESHOLD = 0.40` in attendance.py. Haar cascade + 64×64 cosine similarity on pixel patches **never reaches 0.90** between different shots of the same person. 0.40–0.55 is the practical working range.

## Auto-generate encodings — no session flag

**Do NOT gate with a one-time session flag.** If 0 encodings exist after flag set (photos uploaded mid-session), it blocks retry permanently. Instead check `members_need = [m for m in members if not m.face_encoding]` — skip only when the list is empty.

## PIL fix for camera_input

```python
pil = Image.open(io.BytesIO(cam_img.getvalue()))  # correct
# NOT: Image.open(cam_img)  — raises PIL error on UploadedFile
```

## Two-phase detection (CPU efficiency)

1. `face_engine.detect_faces(img_bgr)` — Haar cascade only, < 15 ms. If no face boxes: return immediately. Idle CPU ≈ 0.
2. `face_engine.get_encoding(img_bgr)` — only if Phase 1 found boxes. Full 64×64 patch + cosine match.

## Capture saves (unknown/expired)

- Rate-limited: max 10/hour per gym (`face_cap_n_{gym_id}`, `face_cap_t_{gym_id}` session counters)
- Compressed: 240×180 JPEG q=55 → Object Storage `unknown_captures/{gym_id}/{ts}_{type}.jpg`
- DB: `UnknownCapture` table (`gym_id`, `capture_key`, `capture_type`, `member_id`, `member_name`, `captured_at`)
- 3-day auto-delete: `db.cleanup_old_captures(days=3)` → returns keys → `object_store.delete_capture(key)` each
- Cleanup: once per session via `face_cleanup_done` session flag

## Key files

- `gym-app/face_engine.py` — Haar cascade + cosine sim. `SIMILARITY_THRESHOLD = 0.40`.
- `gym-app/gym_pages/attendance.py` — `_face_ss_init`, `_load_encodings`, `_auto_generate_encodings`, `_run_cleanup`, `_save_capture`, `_match_face`, `_result_banner`, `_process_face_image`, `_safe_date`, `_face_camera_fragment` (`@st.fragment`), `render_face_recognition_tab`.
- `gym-app/database.py` — `UnknownCapture` ORM + `add_unknown_capture`, `get_unknown_captures`, `delete_unknown_capture_record`, `cleanup_old_captures`.
- `gym-app/object_store.py` — `upload_capture`, `get_capture_bytes`, `delete_capture`.
