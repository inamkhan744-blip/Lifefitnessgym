"""
Photo storage helper — member photos.
Priority:
  1. Cloudinary (works on ALL platforms — Replit + Streamlit Cloud)
  2. Replit Object Storage (Replit only)
  3. Local disk (dev fallback)

photo_path in DB can be:
  - A Cloudinary URL  : "https://res.cloudinary.com/..."  → shown directly
  - An object key     : "member_photos/PF-00001.jpg"      → Object Storage / disk
"""
import os
import io
import uuid
import base64
import streamlit as st

# ── Cloudinary setup ────────────────────────────────────────────────────────
_CLOUDINARY_CLOUD = os.environ.get("CLOUDINARY_CLOUD_NAME", "w7xq1ogn")
_CLOUDINARY_KEY   = os.environ.get("CLOUDINARY_API_KEY", "864276279865347")
_CLOUDINARY_SEC   = os.environ.get("CLOUDINARY_API_SECRET", "")
CLOUDINARY_AVAILABLE = bool(_CLOUDINARY_CLOUD and _CLOUDINARY_KEY and _CLOUDINARY_SEC)

if CLOUDINARY_AVAILABLE:
    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=_CLOUDINARY_CLOUD,
            api_key=_CLOUDINARY_KEY,
            api_secret=_CLOUDINARY_SEC,
            secure=True,
        )
    except Exception:
        CLOUDINARY_AVAILABLE = False

# ── Replit Object Storage setup ─────────────────────────────────────────────
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


# ── Image helpers ────────────────────────────────────────────────────────────
def _compress_image(file_bytes: bytes, max_px: int = 800, quality: int = 72) -> bytes:
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return file_bytes


def _to_display_jpeg(raw: bytes, max_px: int = 400) -> bytes:
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


def _is_url(path: str) -> bool:
    return bool(path) and (path.startswith("http://") or path.startswith("https://"))


# ── Cloudinary helpers ───────────────────────────────────────────────────────
def _cloudinary_upload(image_bytes: bytes, public_id: str) -> str | None:
    """Upload bytes to Cloudinary, return secure URL or None."""
    if not CLOUDINARY_AVAILABLE:
        return None
    try:
        import cloudinary.uploader
        result = cloudinary.uploader.upload(
            image_bytes,
            public_id=public_id,
            folder="gymapp_members",
            overwrite=True,
            resource_type="image",
        )
        return result.get("secure_url")
    except Exception:
        return None


def _cloudinary_delete(public_id: str):
    if not CLOUDINARY_AVAILABLE:
        return
    try:
        import cloudinary.uploader
        cloudinary.uploader.destroy(f"gymapp_members/{public_id}")
    except Exception:
        pass


def _cloudinary_fetch_bytes(url: str) -> bytes | None:
    """Download image from any URL (Cloudinary or otherwise)."""
    try:
        import requests
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None


# ── Core download ─────────────────────────────────────────────────────────────
def _download_raw(key: str) -> bytes | None:
    """Download photo bytes from wherever they are stored."""
    if not key:
        return None

    # 1. Direct URL (Cloudinary or any https URL)
    if _is_url(key):
        return _cloudinary_fetch_bytes(key)

    filename = os.path.basename(key)

    # 2. Replit Object Storage
    if STORAGE_AVAILABLE:
        try:
            return _client.download_as_bytes(key)
        except Exception:
            pass

    # 3. Local disk
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


# ── Public API ───────────────────────────────────────────────────────────────
def upload_photo(file_bytes: bytes, original_name: str, serial: str = "") -> str:
    """
    Photo compress karke upload karo.
    Returns: Cloudinary URL (if available) or object key.
    """
    compressed = _compress_image(file_bytes)
    name = f"{serial}.jpg" if serial else f"{uuid.uuid4().hex}.jpg"
    public_id = name.replace(".jpg", "")
    key = f"{PHOTO_PREFIX}{name}"

    # 1. Try Cloudinary first
    if CLOUDINARY_AVAILABLE:
        url = _cloudinary_upload(compressed, public_id)
        if url:
            return url

    # 2. Replit Object Storage
    if STORAGE_AVAILABLE:
        try:
            _client.upload_from_bytes(key, compressed)
            return key
        except Exception:
            pass

    # 3. Local disk
    local_path = os.path.join(_LOCAL_UPLOADS, os.path.basename(key))
    with open(local_path, "wb") as f:
        f.write(compressed)
    return key


def rename_photo(old_key: str, new_key: str) -> bool:
    """Photo ko naye serial-based key mein move karo."""
    if not old_key or not new_key or old_key == new_key:
        return False

    # Cloudinary URL → update public_id
    if _is_url(old_key) and CLOUDINARY_AVAILABLE:
        # Already on Cloudinary with correct public_id from upload, skip rename
        return True

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


@st.cache_data(ttl=300, show_spinner=False)
def get_photo_bytes(key: str) -> bytes | None:
    """
    Photo download karo as compressed bytes.
    st.image() ke saath directly use karo.
    5-minute cache.
    """
    raw = _download_raw(key)
    if raw is None:
        return None
    # URLs se aaya data already compressed — skip re-compress for URLs
    if _is_url(key):
        return raw
    return _to_display_jpeg(raw)


def get_photo_b64(key: str) -> tuple[str | None, str]:
    """Photo as base64 string. Returns (b64, mime) or (None, '')."""
    data = get_photo_bytes(key)
    if data is None:
        return None, ""
    return base64.b64encode(data).decode(), "jpeg"


def migrate_local_to_storage(local_path: str) -> str | None:
    """Purani local photo ko storage mein move karo."""
    if not os.path.exists(local_path):
        return None
    try:
        with open(local_path, "rb") as f:
            data = f.read()
        return upload_photo(data, os.path.basename(local_path))
    except Exception:
        return None


def migrate_object_storage_to_cloudinary(photo_path: str) -> str | None:
    """
    Object Storage key se photo download karke Cloudinary pe upload karo.
    Returns new Cloudinary URL or None.
    """
    if not photo_path or _is_url(photo_path):
        return photo_path  # Already a URL, nothing to do
    if not CLOUDINARY_AVAILABLE:
        return None
    raw = _download_raw(photo_path)
    if not raw:
        return None
    filename = os.path.basename(photo_path)
    public_id = filename.replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
    return _cloudinary_upload(raw, public_id)


def delete_photo(key: str):
    """Photo delete karo storage se."""
    if not key:
        return
    if _is_url(key) and CLOUDINARY_AVAILABLE:
        # Extract public_id from URL
        try:
            filename = key.split("/")[-1].split(".")[0]
            _cloudinary_delete(filename)
        except Exception:
            pass
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
    """Unknown/expired capture save karo."""
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
    return _download_raw(key)


def delete_capture(key: str):
    delete_photo(key)
