"""
Lightweight Face Detection & Recognition Engine
Uses OpenCV Haar Cascade + cosine similarity — no heavy ML downloads required.
cv2 is imported lazily (on first use) to avoid crashing the production container
during startup in Cloud Run's gVisor sandbox.
"""
import json
from PIL import Image

SIMILARITY_THRESHOLD = 0.40
_cascade = None
_cv2 = None
_np = None


def _get_cv2():
    global _cv2
    if _cv2 is None:
        import cv2 as _cv2_mod
        _cv2 = _cv2_mod
    return _cv2


def _get_np():
    global _np
    if _np is None:
        import numpy as _np_mod
        _np = _np_mod
    return _np


def _get_cascade():
    global _cascade
    cv2 = _get_cv2()
    if _cascade is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _cascade = cv2.CascadeClassifier(path)
    return _cascade


def pil_to_bgr(pil_img: Image.Image):
    cv2 = _get_cv2()
    np = _get_np()
    arr = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def detect_faces(img_bgr) -> list:
    """Returns list of (x, y, w, h) rectangles for every detected face."""
    cv2 = _get_cv2()
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = _get_cascade().detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    return list(faces) if len(faces) > 0 else []


def _extract_face_crop(img_bgr):
    """Crop the largest face to a normalized 64x64 grayscale patch."""
    cv2 = _get_cv2()
    faces = detect_faces(img_bgr)
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    pad = int(min(w, h) * 0.20)
    x1 = max(0, x - pad);  y1 = max(0, y - pad)
    x2 = min(img_bgr.shape[1], x + w + pad)
    y2 = min(img_bgr.shape[0], y + h + pad)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    crop = gray[y1:y2, x1:x2]
    face64 = cv2.resize(crop, (64, 64), interpolation=cv2.INTER_AREA)
    return cv2.equalizeHist(face64)


def get_encoding(img_bgr):
    """
    Extract face encoding: 4096-float unit vector from normalized face patch.
    Returns None if no face is detected.
    """
    np = _get_np()
    face = _extract_face_crop(img_bgr)
    if face is None:
        return None
    flat = face.flatten().astype(np.float32)
    norm = np.linalg.norm(flat)
    if norm > 0:
        flat /= norm
    return flat.tolist()


def get_encoding_from_pil(pil_img: Image.Image):
    return get_encoding(pil_to_bgr(pil_img))


def similarity(enc1: list, enc2: list) -> float:
    """Cosine similarity between two encodings (0-1, higher = more similar)."""
    if not enc1 or not enc2:
        return 0.0
    np = _get_np()
    a = np.array(enc1, dtype=np.float32)
    b = np.array(enc2, dtype=np.float32)
    return float(max(0.0, np.dot(a, b)))


def encoding_to_str(enc: list) -> str:
    return json.dumps(enc)


def str_to_encoding(s: str):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def annotate(img_bgr, label: str = "", color=(0, 255, 0)):
    """Draw face bounding box(es) + label."""
    cv2 = _get_cv2()
    faces = detect_faces(img_bgr)
    out = img_bgr.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
        if label:
            cv2.putText(out, label[:24], (x, max(y - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return out
