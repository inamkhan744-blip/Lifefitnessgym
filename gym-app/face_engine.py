"""
Lightweight Face Detection & Recognition Engine
Uses OpenCV Haar Cascade + cosine similarity — no heavy ML downloads required.
"""
import cv2
import numpy as np
import json
from PIL import Image

SIMILARITY_THRESHOLD = 0.40   # Haar cascade cosine sim — 0.40 is realistic threshold
_cascade = None


def _get_cascade() -> cv2.CascadeClassifier:
    global _cascade
    if _cascade is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _cascade = cv2.CascadeClassifier(path)
    return _cascade


def pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
    arr = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def detect_faces(img_bgr: np.ndarray) -> list:
    """Returns list of (x, y, w, h) rectangles for every detected face."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = _get_cascade().detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    return list(faces) if len(faces) > 0 else []


def _extract_face_crop(img_bgr: np.ndarray) -> np.ndarray | None:
    """Crop the largest face to a normalized 64×64 grayscale patch."""
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


def get_encoding(img_bgr: np.ndarray) -> list[float] | None:
    """
    Extract face encoding: 4 096-float unit vector from normalized face patch.
    Returns None if no face is detected.
    """
    face = _extract_face_crop(img_bgr)
    if face is None:
        return None
    flat = face.flatten().astype(np.float32)
    norm = np.linalg.norm(flat)
    if norm > 0:
        flat /= norm
    return flat.tolist()


def get_encoding_from_pil(pil_img: Image.Image) -> list[float] | None:
    return get_encoding(pil_to_bgr(pil_img))


def similarity(enc1: list[float], enc2: list[float]) -> float:
    """Cosine similarity between two encodings (0 – 1, higher = more similar)."""
    if not enc1 or not enc2:
        return 0.0
    a = np.array(enc1, dtype=np.float32)
    b = np.array(enc2, dtype=np.float32)
    return float(max(0.0, np.dot(a, b)))


def encoding_to_str(enc: list[float]) -> str:
    return json.dumps(enc)


def str_to_encoding(s: str) -> list[float] | None:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def annotate(img_bgr: np.ndarray, label: str = "", color=(0, 255, 0)) -> np.ndarray:
    """Draw face bounding box(es) + label."""
    faces = detect_faces(img_bgr)
    out = img_bgr.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
        if label:
            cv2.putText(out, label[:24], (x, max(y - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return out
