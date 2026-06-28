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


def _compress_image(file_bytes: bytes, max_px: int = 800, quality: int = 72) -> bytes:
    """
    Photo compress karo upload se pehle.
    - Max dimension: 800px (width ya height, jo bhi zyada ho)
    - JPEG quality: 72 (original size ka ~15-25%)
    - EXIF orientation fix included
    """
    try:
        from PIL import Image, ExifTags
        import io

        img = Image.open(io.BytesIO(file_bytes))

        # EXIF orientation fix (phone camera photos seedhe ho jayein)
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

        # Resize: max_px ki limit mein raho, aspect ratio same rakho
        img.thumbnail((max_px, max_px), Image.LANCZOS)

        # RGBA → RGB (JPEG mein alpha channel nahi hoti)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return file_bytes  # Agar kuch fail ho to original return karo


def upload_photo(file_bytes: bytes, original_name: str) -> str:
    """
    Photo compress karke Object Storage mein upload karo.
    Returns: object key like 'member_photos/abc123.jpg'
    """
    # Pehle compress karo — size dramatically kam ho jayega
    compressed = _compress_image(file_bytes)

    # Hamesha .jpg save karo (compressed JPEG hai)
    key = f"{PHOTO_PREFIX}{uuid.uuid4().hex}.jpg"

    if STORAGE_AVAILABLE:
        try:
            _client.upload_from_bytes(key, compressed)
            return key
        except Exception:
            pass

    # Fallback: local disk
    local_path = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
    with open(local_path, "wb") as f:
        f.write(compressed)
    return key


def _to_display_jpeg(raw: bytes, max_px: int = 400) -> bytes:
    """
    Raw bytes ko display ke liye compress karo.
    Max 400px, quality 75 — browser easily render karta hai.
    """
    try:
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(raw))
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=75, optimize=True)
        return buf.getvalue()
    except Exception:
        return raw


def get_photo_b64(key: str) -> tuple[str | None, str]:
    """
    Photo download karo as base64 (display size — compressed).
    Returns (b64_string, mime_type) or (None, '')
    """
    if not key:
        return None, ""

    filename = os.path.basename(key)

    raw = None

    # 1. Object Storage se try karo
    if STORAGE_AVAILABLE:
        try:
            raw = _client.download_as_bytes(key)
        except Exception:
            raw = None

    # 2. Local uploads fallback
    if raw is None:
        for local_path in [
            os.path.join(_LOCAL_UPLOADS, filename),
            key if os.path.isabs(key) else None,
        ]:
            if local_path and os.path.exists(local_path):
                try:
                    with open(local_path, "rb") as f:
                        raw = f.read()
                    break
                except Exception:
                    pass

    if raw is None:
        return None, ""

    # Display ke liye compress karo (4MB → ~15KB)
    display_bytes = _to_display_jpeg(raw)
    return base64.b64encode(display_bytes).decode(), "jpeg"


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
