"""
Replit Object Storage helper — member photos permanent storage.
Sabhi photos GCS bucket mein save hoti hain, restart ke baad bhi safe.
"""
import os
import io
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

_LOCAL_UPLOADS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads"
)
os.makedirs(_LOCAL_UPLOADS, exist_ok=True)


def _compress_image(file_bytes: bytes, max_px: int = 800, quality: int = 72) -> bytes:
    """Upload se pehle compress — EXIF fix, resize, JPEG."""
    try:
        from PIL import Image, ExifTags
        img = Image.open(io.BytesIO(file_bytes))
        try:
            for tag, name in ExifTags.TAGS.items():
                if name == "Orientation":
                    exif = img._getexif()
                    if exif and tag in exif:
                        orientation = exif[tag]
                        rotations = {3: 180, 6: 270, 8: 90}
                        if orientation in rotations:
                            img = img.rotate(rotations[orientation], expand=True)
                    break
        except Exception:
            pass
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return file_bytes


def _to_display_jpeg(raw: bytes, max_px: int = 400) -> bytes:
    """Display ke liye resize — max 400px, quality 75."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        return buf.getvalue()
    except Exception:
        return raw


def _download_raw(key: str) -> bytes | None:
    """Object Storage ya local disk se raw bytes download karo."""
    if not key:
        return None
    filename = os.path.basename(key)

    if STORAGE_AVAILABLE:
        try:
            return _client.download_as_bytes(key)
        except Exception:
            pass

    for local_path in [
        os.path.join(_LOCAL_UPLOADS, filename),
        key if os.path.isabs(key) else None,
    ]:
        if local_path and os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    return f.read()
            except Exception:
                pass
    return None


def upload_photo(file_bytes: bytes, original_name: str, serial: str = "") -> str:
    """
    Photo compress karke Object Storage mein upload karo.
    serial dene par key = member_photos/{serial}.jpg
    Returns: object key like 'member_photos/PF-00001.jpg'
    """
    compressed = _compress_image(file_bytes)
    name = f"{serial}.jpg" if serial else f"{uuid.uuid4().hex}.jpg"
    key = f"{PHOTO_PREFIX}{name}"

    if STORAGE_AVAILABLE:
        try:
            _client.upload_from_bytes(key, compressed)
            return key
        except Exception:
            pass

    local_path = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
    with open(local_path, "wb") as f:
        f.write(compressed)
    return key


def rename_photo(old_key: str, new_key: str) -> bool:
    """Photo ko naye serial-based key mein move karo."""
    if not old_key or not new_key or old_key == new_key:
        return False
    if STORAGE_AVAILABLE:
        try:
            data = _client.download_as_bytes(old_key)
            _client.upload_from_bytes(new_key, data)
            _client.delete(old_key)
            return True
        except Exception:
            pass
    local_old = os.path.join(_LOCAL_UPLOADS, os.path.basename(old_key))
    local_new = os.path.join(_LOCAL_UPLOADS, os.path.basename(new_key))
    if os.path.exists(local_old):
        try:
            os.rename(local_old, local_new)
            return True
        except Exception:
            pass
    return False


def get_photo_bytes(key: str) -> bytes | None:
    """
    Photo download karo as compressed bytes (display size).
    st.image() ke saath directly use karo.
    Returns None agar photo nahi mili.
    """
    raw = _download_raw(key)
    if raw is None:
        return None
    return _to_display_jpeg(raw)


def get_photo_b64(key: str) -> tuple[str | None, str]:
    """Photo as base64 string. Returns (b64, mime) or (None, '')."""
    data = get_photo_bytes(key)
    if data is None:
        return None, ""
    return base64.b64encode(data).decode(), "jpeg"


def migrate_local_to_storage(local_path: str) -> str | None:
    """Purani local photo ko Object Storage mein move karo."""
    if not os.path.exists(local_path):
        return None
    try:
        with open(local_path, "rb") as f:
            data = f.read()
        return upload_photo(data, os.path.basename(local_path))
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
    local = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
    if os.path.exists(local):
        try:
            os.remove(local)
        except Exception:
            pass


CAPTURE_PREFIX = "unknown_captures/"

def upload_capture(key: str, image_bytes: bytes) -> bool:
    """
    Unknown/expired capture ko Object Storage mein save karo.
    key = 'unknown_captures/{gym_id}/{timestamp}_{type}.jpg'
    Returns True on success.
    """
    if not key or not image_bytes:
        return False
    try:
        if STORAGE_AVAILABLE:
            _client.upload_from_bytes(key, image_bytes)
            return True
        local = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
        with open(local, "wb") as f:
            f.write(image_bytes)
        return True
    except Exception:
        return False


def get_capture_bytes(key: str) -> bytes | None:
    """Capture image download karo for display."""
    return _download_raw(key)


def delete_capture(key: str):
    """Capture delete karo — same as delete_photo."""
    delete_photo(key)
