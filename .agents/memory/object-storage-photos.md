---
name: Object Storage for photos
description: How member photos are stored permanently using Replit Object Storage
---

# Member Photo Storage — Replit Object Storage

## Setup
- Bucket provisioned via `setupObjectStorage()` — bucket ID in env var `DEFAULT_OBJECT_STORAGE_BUCKET_ID`
- Python client: `replit-object-storage` package (in requirements.txt)
- Helper module: `gym-app/object_store.py`

## Key functions in object_store.py
- `upload_photo(file_bytes, original_name)` → returns key like `member_photos/abc123.jpg`
- `get_photo_b64(key)` → returns `(base64_string, mime_type)` tuple
- `delete_photo(key)` → removes from Object Storage + local fallback
- `migrate_local_to_storage(local_path)` → uploads local file, returns new key
- `STORAGE_AVAILABLE` — bool, False if bucket not configured

## Rules
- `save_photo()` in members.py calls `object_store.upload_photo()` — returns storage key, NOT a file path
- DB stores the key (e.g. `member_photos/abc123.jpg`), NOT a local path
- `show_photo()` calls `object_store.get_photo_b64()` — works from Object Storage first, local fallback second
- `update_member_photo_path()` in database.py stores the key as-is (no `gym-app/uploads/` prefix)
- Client must be initialized with `bucket_id=os.environ.get("DEFAULT_OBJECT_STORAGE_BUCKET_ID")`

**Why:** Replit filesystem is ephemeral — local uploads/ folder is lost on server restart. Object Storage persists permanently, even after Autoscale restarts.

**How to apply:** Any new page that handles member photos must import `object_store` and use its functions. Never save photos to local disk only.
