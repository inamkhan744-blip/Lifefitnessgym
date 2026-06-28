"""
Replit Object Storage helper — member photos permanent storage.
Sabhi photos GCS bucket mein save hoti hain, restart ke baad bhi safe.
"""
import os
import uuid
import base64

try:
    from replit.object_storage import Client as _ObjClient
    _BUCKET_ID = os.environ.get("DEFAULT_OBJECT_STORAGE_BUCKET_ID")
    _client = _ObjClient(bucket_id=_BUCKET_ID) if _BUCKET_ID else None
    STORAGE_AVAILABLE = _client is not None
except Exception:
    _client = None
    STORAGE_AVAILABLE = False

PHOTO_PREFIX = "member_photos/"

# Absolute local fallback path (sirf backup ke liye)
_LOCAL_UPLOADS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads"
)
os.makedirs(_LOCAL_UPLOADS, exist_ok=True)


def upload_photo(file_bytes: bytes, original_name: str) -> str:
    """
    Photo upload karo — Object Storage mein.
    Returns: object key like 'member_photos/abc123.jpg'
    """
    ext = os.path.splitext(original_name)[-1].lower() or ".jpg"
    key = f"{PHOTO_PREFIX}{uuid.uuid4().hex}{ext}"

    if STORAGE_AVAILABLE:
        try:
            _client.upload_from_bytes(key, file_bytes)
            return key
        except Exception:
            pass

    # Fallback: local disk
    local_path = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    return key


def get_photo_b64(key: str) -> tuple[str | None, str]:
    """
    Photo download karo as base64.
    Returns (b64_string, mime_type) or (None, '')
    """
    if not key:
        return None, ""

    filename = os.path.basename(key)
    ext = os.path.splitext(filename)[-1].lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")

    # 1. Object Storage se try karo
    if STORAGE_AVAILABLE:
        try:
            data = _client.download_as_bytes(key)
            return base64.b64encode(data).decode(), mime
        except Exception:
            pass

    # 2. Local uploads fallback
    for local_path in [
        os.path.join(_LOCAL_UPLOADS, filename),
        key if os.path.isabs(key) else None,
    ]:
        if local_path and os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    data = f.read()
                return base64.b64encode(data).decode(), mime
            except Exception:
                pass

    return None, ""


def migrate_local_to_storage(local_path: str) -> str | None:
    """
    Purani local photo ko Object Storage mein move karo.
    Returns new key, or None if failed.
    """
    if not os.path.exists(local_path):
        return None
    try:
        with open(local_path, "rb") as f:
            data = f.read()
        key = upload_photo(data, os.path.basename(local_path))
        return key
    except Exception:
        return None


def delete_photo(key: str):
    """Photo delete karo storage se."""
    if not key:
        return
    if STORAGE_AVAILABLE:
        try:
            _client.delete(key)
        except Exception:
            pass
    # Local bhi hatao
    local = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
    if os.path.exists(local):
        try:
            os.remove(local)
        except Exception:
            pass
