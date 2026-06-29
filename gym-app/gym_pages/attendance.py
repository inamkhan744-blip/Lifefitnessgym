import streamlit as st
import os
import base64
from datetime import date, datetime, timedelta
import pandas as pd
import time
import object_store
import face_engine
from PIL import Image
import io
import numpy as np

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

import database as db
import styles

# ── FIX: Photo path helper ────────────────────────────────────────────────
UPLOAD_DIR = "gym-app/uploads"

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

def init_session_state():
    """Initialize all session state variables"""
    if 'attendance_photo_cache' not in st.session_state:
        st.session_state.attendance_photo_cache = {}
    if 'gallery_loaded' not in st.session_state:
        st.session_state.gallery_loaded = False
    if 'gallery_html' not in st.session_state:
        st.session_state.gallery_html = []
    if 'selected_member_id' not in st.session_state:
        st.session_state.selected_member_id = None
    if 'photo_cache' not in st.session_state:
        st.session_state.photo_cache = {}
    if '_member_count' not in st.session_state:
        st.session_state._member_count = 0
    if 'all_members_data' not in st.session_state:
        st.session_state.all_members_data = []
    if 'face_enabled' not in st.session_state:
        st.session_state.face_enabled = True
    if 'face_idle_count' not in st.session_state:
        st.session_state.face_idle_count = 0
    if 'face_idle_mode' not in st.session_state:
        st.session_state.face_idle_mode = False
    if 'face_last_result' not in st.session_state:
        st.session_state.face_last_result = None
    if 'face_enc_cache' not in st.session_state:
        st.session_state.face_enc_cache = None
    if 'face_enc_cache_ts' not in st.session_state:
        st.session_state.face_enc_cache_ts = 0.0
    if 'face_enc_cache_gym' not in st.session_state:
        st.session_state.face_enc_cache_gym = None

# Initialize session state
init_session_state()

# ============================================
# 🖼️ IMAGE ORIENTATION FIX
# ============================================

def fix_image_orientation(img):
    """Fix image orientation using EXIF data"""
    try:
        if hasattr(img, '_getexif'):
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)
                if orientation:
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
    except:
        pass
    return img

def compress_image_with_orientation(image_path, max_size_kb=50, quality=70):
    """Compress image with orientation fix"""
    try:
        img = Image.open(image_path)
        img = fix_image_orientation(img)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        max_width = 400
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        while len(output.getvalue()) > max_size_kb * 1024 and quality > 20:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
    except Exception as e:
        print(f"Image compression error: {e}")
        return None

def get_attendance_photo_b64(photo_field: str, serial_number: str = "") -> str | None:
    """Get compressed photo with orientation fix"""
    init_session_state()

    cache_key = f"attendance_{serial_number}_{photo_field}"
    if cache_key in st.session_state.attendance_photo_cache:
        return st.session_state.attendance_photo_cache[cache_key]

    # 1. Object Storage — primary source
    for key in filter(None, [photo_field, f"member_photos/{serial_number}.jpg" if serial_number else None]):
        try:
            b64, _ = object_store.get_photo_b64(key)
            if b64:
                result = f"data:image/jpeg;base64,{b64}"
                st.session_state.attendance_photo_cache[cache_key] = result
                return result
        except Exception:
            pass

    # 2. Local filesystem fallback
    photo_path = None
    if photo_field:
        photo_str = str(photo_field).strip()
        if "<div" not in photo_str and "style=" not in photo_str:
            filename = os.path.basename(photo_str)
            for path in [os.path.join(UPLOAD_DIR, filename), os.path.join("gym-app/uploads", filename), photo_str]:
                if path and os.path.exists(path) and os.path.isfile(path):
                    photo_path = path
                    break

    if not photo_path and serial_number:
        clean_serial = str(serial_number).strip().replace("-", "").lower()
        if os.path.exists(UPLOAD_DIR):
            for file_name in os.listdir(UPLOAD_DIR):
                if clean_serial in file_name.lower().replace("_", "").replace("-", ""):
                    path = os.path.join(UPLOAD_DIR, file_name)
                    if os.path.isfile(path):
                        photo_path = path
                        break

    if photo_path:
        compressed_data = compress_image_with_orientation(photo_path)
        if compressed_data:
            b64 = f"data:image/jpeg;base64,{base64.b64encode(compressed_data).decode()}"
            st.session_state.attendance_photo_cache[cache_key] = b64
            return b64

    return None

def get_photo_path(filename):
    """Convert filename to full path for display"""
    if not filename:
        return None
    if os.path.exists(filename):
        return filename
    full_path = os.path.join(UPLOAD_DIR, filename)
    return full_path if os.path.exists(full_path) else None

def show_member_photo(photo_field, width=100):
    """Safely display member photo with orientation fix - SQUARE FRAME"""
    init_session_state()
    
    if photo_field:
        photo_b64 = get_attendance_photo_b64(photo_field, "")
        if photo_b64:
            st.markdown(
                f'''
                <div style="width:{width}px; height:{width}px;
                            border:3px solid #7C3AED; overflow:hidden;
                            background:#1E293B; flex-shrink:0;
                            border-radius:8px;">
                    <img src="{photo_b64}" style="width:100%; height:100%;
                                                  object-fit:cover; display:block;" />
                </div>
                ''',
                unsafe_allow_html=True
            )
            return True
        
        path = get_photo_path(photo_field)
        if path:
            try:
                compressed = compress_image_with_orientation(path)
                if compressed:
                    b64 = base64.b64encode(compressed).decode()
                    st.markdown(
                        f'''
                        <div style="width:{width}px; height:{width}px;
                                    border:3px solid #7C3AED; overflow:hidden;
                                    background:#1E293B; flex-shrink:0;
                                    border-radius:8px;">
                            <img src="data:image/jpeg;base64,{b64}" style="width:100%; height:100%;
                                                                          object-fit:cover; display:block;" />
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                    return True
            except Exception:
                pass
    
    st.markdown(
        f"""
        <div style="width:{width}px; height:{width}px;
                    background:#334155; display:flex;
                    align-items:center; justify-content:center;
                    font-size:{width//2}px; color:#94A3B8;
                    flex-shrink:0; border-radius:8px;
                    border:3px solid #7C3AED44;">
            👤
        </div>
        """,
        unsafe_allow_html=True
    )
    return False

# ── Audio ────────────────────────────────────────────────────────────────────
_AUDIO_PRIMER_JS = """
<script>
(function(){
  const W = window.parent;
  if (W._gymAudioPrimed) return;
  W._gymAudioPrimed = true;
  const ensure = () => {
    if (!W._gymAudioCtx) {
      try {
        W._gymAudioCtx = new (W.AudioContext || W.webkitAudioContext)();
      } catch(e) { return; }
    }
    if (W._gymAudioCtx.state === "suspended") {
      W._gymAudioCtx.resume().catch(()=>{});
    }
  };
  ensure();
  ["click","keydown","touchstart"].forEach(ev =>
    W.parent && W.parent.document
      ? W.parent.document.addEventListener(ev, ensure, {once:false, passive:true})
      : W.document.addEventListener(ev, ensure, {once:false, passive:true})
  );
})();
</script>
"""

def _tone_js(freq: int, dur_ms: int, wave: str, gain: float) -> str:
    return f"""
<script>
(function(){{
  try {{
    const W = window.parent;
    let ctx = W._gymAudioCtx;
    if (!ctx) {{
      ctx = new (W.AudioContext || W.webkitAudioContext)();
      W._gymAudioCtx = ctx;
    }}
    if (ctx.state === "suspended") ctx.resume().catch(()=>{{}});
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "{wave}"; o.frequency.value = {freq};
    g.gain.value = {gain};
    o.connect(g); g.connect(ctx.destination);
    o.start();
    o.stop(ctx.currentTime + {dur_ms / 1000.0});
  }} catch(e) {{}}
}})();
</script>
"""

_BEEP_JS = _tone_js(880, 180, "sine", 0.18)
_BUZZ_JS = _tone_js(180, 450, "square", 0.22)

def _play(kind: str):
    st.components.v1.html(_BEEP_JS if kind == "beep" else _BUZZ_JS, height=0)

def _autofocus_scan_input():
    st.components.v1.html(
        """
        <script>
        (function(){
          const focusIt = () => {
            const doc = window.parent.document;
            let el = doc.querySelector('input[aria-label="Scan member QR code"]');
            if (!el) {
              const form = doc.querySelector('form[data-testid="stForm"]');
              if (form) el = form.querySelector('input[type="text"]');
            }
            if (el) { el.focus(); el.select && el.select(); }
          };
          focusIt();
          setTimeout(focusIt, 100);
          setTimeout(focusIt, 400);
        })();
        </script>
        """,
        height=0,
    )

def _big_banner(color_bg: str, color_border: str, headline: str,
                subline: str = "", icon: str = ""):
    st.markdown(
        f"""
        <div style="background:{color_bg};border:3px solid {color_border};
                    border-radius:18px;padding:1.8rem 1.5rem;text-align:center;
                    margin:1rem 0;box-shadow:0 12px 35px rgba(0,0,0,0.45);">
          <div style="font-size:3.4rem;line-height:1;">{icon}</div>
          <div style="font-size:2.2rem;font-weight:900;color:#fff;
                      letter-spacing:0.02em;margin-top:0.4rem;">
            {headline}
          </div>
          <div style="font-size:1.05rem;color:#F8FAFC;opacity:0.9;
                      margin-top:0.5rem;">{subline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _process_scan(raw: str, gym_id, current_user) -> dict:
    serial = (raw or "").strip()
    if not serial:
        return {"kind": "error", "headline": "EMPTY SCAN",
                "sub": "No code received."}

    member = db.get_member_by_serial(serial, gym_id=gym_id)
    if not member:
        global_match = db.get_member_by_serial(serial)
        if global_match:
            return {
                "kind": "error",
                "headline": "WRONG GYM",
                "sub": f"{global_match.full_name} ({serial}) belongs to a "
                       f"different gym. Switch gym selector.",
            }
        return {"kind": "error", "headline": "MEMBER NOT FOUND",
                "sub": f"No member with code '{serial}'."}

    if (member.status or "").lower() != "active":
        return {
            "kind": "error",
            "headline": f"ACCOUNT {(member.status or 'INACTIVE').upper()}",
            "sub": f"{member.full_name} — please see counter.",
            "member": member,
        }

    if member.expiry_date:
        try:
            exp = date.fromisoformat(member.expiry_date)
            if exp < date.today():
                return {
                    "kind": "expired",
                    "headline": "FEES EXPIRED",
                    "sub": f"PLEASE PAY AT COUNTER · "
                           f"{member.full_name} · expired {member.expiry_date}",
                    "member": member,
                }
        except Exception:
            pass

    ok, msg = db.mark_attendance(member.id, member.gym_id,
                                 date.today(), "Present", current_user)
    if not ok:
        return {"kind": "error", "headline": "DATABASE ERROR",
                "sub": msg, "member": member}

    return {
        "kind": "success",
        "headline": "✓ WELCOME",
        "sub": f"{member.full_name} checked in",
        "member": member,
    }

# ── AI PREDICTION LOGIC ──────────────────────────────────────────────────────
def _get_ai_traffic_insights(recent_scans):
    now = datetime.now()
    current_hour = now.hour

    historical_patterns = {
        6: 4, 7: 6, 8: 5,   
        16: 6, 17: 12, 18: 15, 19: 18, 20: 14, 21: 9, 22: 4 
    }

    current_hour_count = 0
    next_hour_predicted = historical_patterns.get((current_hour + 1) % 24, 5)

    if recent_scans:
        for r in recent_scans:
            try:
                r_hour = int(r["time"].split(":")[0])
                if r_hour == current_hour:
                    current_hour_count += 1
            except Exception:
                pass

    normal_for_this_hour = historical_patterns.get(current_hour, 8)

    return {
        "current_hour_string": now.strftime("%I:00 %p"),
        "next_hour_string": (now + timedelta(hours=1)).strftime("%I:00 %p"),
        "normal_average": normal_for_this_hour,
        "today_actual": current_hour_count,
        "next_predicted": next_hour_predicted,
    }

# ── AI SMART REGISTRATIONS, FEES ──────────────────────────────────────────────
def render_ai_dashboard_intel(sel_gid):
    st.markdown("### 🤖 GymPro AI Smart Security & Analytics Intel")
    
    today_str = date.today().isoformat()
    
    recent_scans = db.get_recent_scans(gym_id=sel_gid, limit=100, today_only=True)
    all_members = db.get_members(gym_id=sel_gid)
    active_members = [m for m in all_members if (m.status or '').lower() == 'active']
    todays_fees = db.get_todays_fees(gym_id=sel_gid)
    
    expiring_soon = [m for m in all_members if m.expiry_date and 
         (date.fromisoformat(m.expiry_date) - date.today()).days <= 7 and
         (date.fromisoformat(m.expiry_date) - date.today()).days >= 0]

    revenue_risk = len(expiring_soon) * 1500 

    col_text1, col_text2 = st.columns(2)
    with col_text1:
        st.info(f"✍️ **AI Registration Summary:**\n\nIs waqt total **{len(all_members)} members** registered hain, jin mein se **{len(active_members)} active** hain.")
    with col_text2:
        st.success(f"💰 **AI Fee Collection Summary:**\n\nAaj ki total collection: **PKR {sum(todays_fees) if todays_fees else 0:,}**.")

    st.markdown("#### 🚨 Fraud & Security Monitor")
    fraud_members = []
    
    if recent_scans:
        for scan in recent_scans:
            member_match = db.get_member_by_serial(scan["serial"], gym_id=sel_gid)
            if member_match and member_match.expiry_date:
                if member_match.expiry_date < today_str and member_match.id not in [m.id for m in fraud_members]:
                    fraud_members.append(member_match)

    if fraud_members:
        st.error(f"🚨 ALERT: Aaj counter par {len(fraud_members)} Unpaid Members ko entry di gayi hai!")
        with st.expander("🔍 Click karein aur Unpaid Members ke Naam aur Pictures dekhein"):
            for m in fraud_members:
                col_pic, col_info = st.columns([1, 4])
                with col_pic:
                    show_member_photo(m.photo_path, width=80)
                with col_info:
                    st.markdown(
                        f"""
                        <div style="padding:10px 0;">
                            <div style="font-weight:bold; color:#F8FAFC; font-size:1.2rem;">{m.full_name}</div>
                            <div style="color:#94A3B8; font-size:0.95rem;">ID: {m.serial_number} | <span style="color:#FCA5A5;">Expired: {m.expiry_date}</span></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.divider()
    else:
        st.success("✅ **AI Security Audit:** Clear! Aaj koi unpaid member entry nahi le paya.")

    st.markdown("#### 🔮 Business Projections & Live Risk Matrix")
    ai_traffic = _get_ai_traffic_insights(recent_scans)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        label="Live Traffic Matrix vs Average", 
        value=f"{ai_traffic['today_actual']} Inside Now", 
        delta=f"Normal Pattern: {ai_traffic['normal_average']}"
    )
    c2.metric(
        label="🔮 Next Hour Load Prediction", 
        value=f"~ {ai_traffic['next_predicted']} Members",
        delta="AI Projected Rush"
    )
    c3.metric(
        label="⚠️ 7-Day Fee Collection Target", 
        value=f"PKR {revenue_risk:,}", 
        delta=f"{len(expiring_soon)} Members Expiring",
        delta_color="inverse"
    )
    st.divider()


# ════════════════════════════════════════════════════════════════════════════
#  FACE RECOGNITION — FIXED VERSION
#  Key fixes:
#  1. Stable camera key (only increments AFTER photo processed, not every tick)
#  2. No run_every (JS click triggers fragment rerun — no double-reset)
#  3. Threshold 0.40 (Haar cascade cosine sim realistic range)
#  4. Auto-generate retries if count=0 even if session flag set
# ════════════════════════════════════════════════════════════════════════════

_ENC_CACHE_TTL   = 300   # seconds — refresh DB encodings
_MEMBER_COOLDOWN = 60    # seconds — prevent double-marking same member
_CAP_RATE_LIMIT  = 10    # max unknown/expired saves per hour
FACE_THRESHOLD   = 0.40  # cosine similarity — realistic for Haar cascade


# ── Session defaults ──────────────────────────────────────────────────────────
def _face_ss_init():
    defs = {
        "face_last_result":   None,
        "face_enc_cache":     None,
        "face_enc_cache_ts":  0.0,
        "face_enc_cache_gym": None,
        "face_cam_gen":       0,    # increments after each processed photo → resets camera
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Encoding cache ────────────────────────────────────────────────────────────
def _load_encodings(gym_id):
    now = time.time()
    stale = (
        st.session_state.face_enc_cache is None
        or st.session_state.face_enc_cache_gym != gym_id
        or now - st.session_state.face_enc_cache_ts > _ENC_CACHE_TTL
    )
    if stale:
        st.session_state.face_enc_cache     = db.get_face_encodings(gym_id)
        st.session_state.face_enc_cache_gym = gym_id
        st.session_state.face_enc_cache_ts  = now
    return st.session_state.face_enc_cache


# ── Auto-generate encodings from profile photos ───────────────────────────────
# Retries every call if count is still 0 (photo might have been uploaded after flag set)
def _auto_generate_encodings(gym_id: int) -> int:
    current = db.get_face_encodings(gym_id)
    members = db.get_members(gym_id=gym_id)
    members_need = [m for m in members if not m.face_encoding]

    if not members_need:
        return 0   # all already have encodings

    generated = 0
    for m in members_need:
        photo_bytes = None
        for key in filter(None, [
            m.photo_path,
            f"member_photos/{m.serial_number}.jpg" if m.serial_number else None,
        ]):
            photo_bytes = object_store.get_photo_bytes(key)
            if photo_bytes:
                break
        if not photo_bytes:
            continue
        try:
            pil = Image.open(io.BytesIO(photo_bytes))
            enc = face_engine.get_encoding_from_pil(pil)
            if enc:
                db.save_face_encoding(m.id, face_engine.encoding_to_str(enc))
                generated += 1
        except Exception:
            pass

    if generated:
        st.session_state.face_enc_cache = None   # invalidate cache
    return generated


# ── 3-day cleanup (once per session) ─────────────────────────────────────────
def _run_cleanup():
    if st.session_state.get("face_cleanup_done"):
        return
    try:
        keys = db.cleanup_old_captures(days=3)
        for key in keys:
            object_store.delete_capture(key)
    except Exception:
        pass
    st.session_state.face_cleanup_done = True


# ── Save unknown/expired snapshot — rate-limited ──────────────────────────────
def _save_capture(pil_img, gym_id, capture_type="unknown",
                  member_id=None, member_name=None):
    try:
        rk = f"face_cap_n_{gym_id}"; rt = f"face_cap_t_{gym_id}"
        now = time.time()
        if now - st.session_state.get(rt, 0) > 3600:
            st.session_state[rk] = 0; st.session_state[rt] = now
        if st.session_state.get(rk, 0) >= _CAP_RATE_LIMIT:
            return
        small = pil_img.resize((240, 180))
        buf   = io.BytesIO()
        small.save(buf, format="JPEG", quality=55, optimize=True)
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"unknown_captures/{gym_id}/{ts}_{capture_type}.jpg"
        if object_store.upload_capture(key, buf.getvalue()):
            db.add_unknown_capture(
                gym_id=gym_id, capture_key=key, capture_type=capture_type,
                member_id=member_id, member_name=member_name,
            )
            st.session_state[rk] = st.session_state.get(rk, 0) + 1
    except Exception:
        pass


# ── Best match using local threshold ─────────────────────────────────────────
def _match_face(encoding, encodings_list):
    best_score, best = 0.0, None
    for m in encodings_list:
        stored = face_engine.str_to_encoding(m["encoding_json"])
        if stored is None:
            continue
        score = face_engine.similarity(encoding, stored)
        if score > best_score:
            best_score, best = score, m
    if best and best_score >= FACE_THRESHOLD:
        return {**best, "score": best_score}
    return None


# ── Result banner ─────────────────────────────────────────────────────────────
def _result_banner(kind: str, name: str = "", detail: str = ""):
    cfg = {
        "success":  ("#064E3B", "#10B981", "✅"),
        "expired":  ("#78350F", "#F59E0B", "⚠️"),
        "unknown":  ("#1E1B4B", "#6366F1", "❓"),
        "noface":   ("#0F172A", "#1E293B", "🎥"),
        "error":    ("#1E293B", "#EF4444", "🚫"),
        "cooldown": ("#064E3B", "#6EE7B7", "✅"),
    }
    bg, border, icon = cfg.get(kind, ("#1E293B", "#475569", "ℹ️"))
    st.markdown(
        f"""<div style="background:{bg};border:3px solid {border};border-radius:16px;
                        padding:1rem;text-align:center;margin:.4rem 0;">
              <div style="font-size:2.2rem;line-height:1">{icon}</div>
              <div style="font-size:1.4rem;font-weight:900;color:#fff;margin-top:.2rem">{name}</div>
              <div style="font-size:.82rem;color:#CBD5E1;margin-top:.2rem">{detail}</div>
            </div>""",
        unsafe_allow_html=True,
    )


# ── Core process: detect → encode → match → mark ─────────────────────────────
def _process_face_image(pil_img, gym_id, current_user):
    # Resize to max 320px wide
    w, h = pil_img.size
    if w > 320:
        pil_img = pil_img.resize((320, int(h * 320 / w)), Image.BILINEAR)

    img_bgr = face_engine.pil_to_bgr(pil_img)

    # Phase 1: fast face-box check (< 15 ms; returns immediately if no face)
    faces = face_engine.detect_faces(img_bgr)
    if not faces:
        return {"kind": "noface", "name": "Koi face nahi mila",
                "detail": "Camera ke bilkul saamne aayein — seedha, achhi light mein"}

    # Phase 2: full encoding + match
    encoding = face_engine.get_encoding(img_bgr)
    if encoding is None:
        return {"kind": "noface", "name": "Encoding fail",
                "detail": "Thoda aur qareeb aayein"}

    encodings = _load_encodings(gym_id)
    if not encodings:
        return {"kind": "error", "name": "KOI PHOTO REGISTERED NAHI",
                "detail": "Members page par member ka photo upload karein"}

    match = _match_face(encoding, encodings)
    if match is None:
        _save_capture(pil_img, gym_id, "unknown")
        return {"kind": "unknown", "name": "UNKNOWN PERSON",
                "detail": f"Match nahi hua (threshold: {FACE_THRESHOLD}) — admin ko alert gaya"}

    # Expired
    if match.get("expiry_date"):
        try:
            if date.fromisoformat(match["expiry_date"]) < date.today():
                _save_capture(pil_img, gym_id, "expired",
                              member_id=match["id"], member_name=match["full_name"])
                return {
                    "kind": "expired", "name": match["full_name"],
                    "detail": f"Membership expired {match['expiry_date']} — counter par aayein",
                    "member": match,
                }
        except Exception:
            pass

    # Inactive
    if (match.get("status") or "active").lower() not in ("active",):
        return {"kind": "error", "name": match["full_name"],
                "detail": f"Account {match.get('status','Inactive')} — counter par aayein",
                "member": match}

    # Cooldown — don't double-mark within 60 s
    cd_key   = f"face_cd_{match['id']}"
    now      = time.time()
    last_hit = st.session_state.get(cd_key, 0)
    if now - last_hit < _MEMBER_COOLDOWN:
        remaining = int(_MEMBER_COOLDOWN - (now - last_hit))
        return {
            "kind": "cooldown", "name": f"WELCOME  {match['full_name']}",
            "detail": f"✅ Aaj pahle hi mark ho gaya · {remaining}s cooldown · {match['serial_number']}",
            "member": match,
        }

    # ✅ Mark attendance
    db.mark_attendance(match["id"], match["gym_id"],
                       date.today(), "Present", current_user)
    st.session_state[cd_key]        = now
    st.session_state.face_enc_cache = None

    return {
        "kind": "success",
        "name": f"WELCOME  {match['full_name']}",
        "detail": f"✅ Attendance mark · {match['score']*100:.0f}% match · {match['serial_number']}",
        "member": match,
    }


def _safe_date(d_str):
    try:
        return date.fromisoformat(d_str)
    except Exception:
        return None


# ── JS auto-click (fires on every fragment render) ────────────────────────────
_AUTOCLICK_JS = (
    "<script>(function(){"
    "if(window._gymFaceClickActive)return;"
    "window._gymFaceClickActive=true;"
    "function _doClick(){"
    "try{"
    "var d=window.parent?window.parent.document:document;"
    "var b=d.querySelectorAll('button');"
    "for(var i=0;i<b.length;i++){"
    "var t=(b[i].innerText||b[i].textContent||'').trim().toLowerCase();"
    "if((t==='take photo'||t.includes('take photo'))&&b[i].offsetParent!==null&&!b[i].disabled)"
    "{b[i].click();return;}"
    "}}"
    "catch(e){}"
    "}"
    "setTimeout(_doClick,600);"
    "setTimeout(_doClick,1400);"
    "setInterval(_doClick,5000);"
    "})();</script>"
)


# ── Fragment — isolated section; reruns only on widget change (JS click) ──────
# NO run_every: the JS auto-click fires → "Take Photo" → widget change → rerun
# After processing we increment face_cam_gen → camera key changes → widget resets
# → JS fires again → new photo → repeat (clean loop, no double-reset)
@st.fragment
def _face_camera_fragment(face_gym_id, current_user, role, gyms):
    # Inject auto-click JS every render
    st.components.v1.html(_AUTOCLICK_JS, height=0)

    cam_col, stat_col = st.columns([6, 4], gap="medium")

    with cam_col:
        st.markdown("##### 📷 Auto Face Recognition")
        st.caption("🔁 JS clicks 'Take Photo' every 5 s automatically")

        # Stable key — only changes AFTER a photo is processed (not on a timer)
        cam_gen = st.session_state.face_cam_gen
        cam_img = st.camera_input(
            "Camera",
            key=f"fac_{cam_gen}",
            label_visibility="collapsed",
        )

        if cam_img is not None:
            try:
                pil = Image.open(io.BytesIO(cam_img.getvalue()))
            except Exception:
                pil = None

            if pil:
                with st.spinner("🔍 Scanning..."):
                    result = _process_face_image(pil, face_gym_id, current_user)

                st.session_state.face_last_result = result

                # Always advance the camera gen so the widget resets for next shot
                st.session_state.face_cam_gen += 1

                # Annotate frame
                try:
                    img_bgr = face_engine.pil_to_bgr(pil)
                    _cmap = {
                        "success":  (0, 220, 100), "cooldown": (0, 220, 100),
                        "expired":  (0, 180, 255), "unknown":  (200, 60, 220),
                        "error":    (60, 60, 255), "noface":   (80, 80, 80),
                    }
                    ann     = face_engine.annotate(
                        img_bgr,
                        result["name"][:22],
                        _cmap.get(result["kind"], (200, 200, 200)),
                    )
                    ann_pil = Image.fromarray(cv2.cvtColor(ann, cv2.COLOR_BGR2RGB))
                    st.image(ann_pil, use_container_width=True)
                except Exception:
                    st.image(pil, use_container_width=True)

                _result_banner(result["kind"], result["name"], result["detail"])

                if result["kind"] == "success":
                    st.components.v1.html(_BEEP_JS, height=0)
                elif result["kind"] in ("expired", "unknown"):
                    st.components.v1.html(_BUZZ_JS, height=0)

                # Rerun fragment so camera resets immediately (key already incremented)
                st.rerun(scope="fragment")

        else:
            lr = st.session_state.face_last_result
            if lr and lr["kind"] != "noface":
                _result_banner(lr["kind"], lr["name"], lr["detail"])
            else:
                st.markdown(
                    '<div style="background:#0F172A;border:2px dashed #1E293B;'
                    'border-radius:12px;padding:2rem;text-align:center;color:#475569;">'
                    "🎥 Camera ready — JS will auto-click 'Take Photo' in a moment"
                    "</div>",
                    unsafe_allow_html=True,
                )

    # ── Stats sidebar ─────────────────────────────────────────────────────────
    with stat_col:
        st.markdown("##### 📊 Live Summary")
        enrolled      = _load_encodings(face_gym_id)
        all_today_att = db.get_attendance(gym_id=face_gym_id, check_date=date.today())
        present_today = [r for r in all_today_att if r.status == "Present"]
        all_members   = db.get_members(gym_id=face_gym_id)
        expired_mems  = [
            m for m in all_members
            if m.expiry_date and _safe_date(m.expiry_date) is not None
            and _safe_date(m.expiry_date) < date.today()
        ]
        captures_db = db.get_unknown_captures(gym_id=face_gym_id, limit=200)
        unk_count   = sum(1 for c in captures_db if c.capture_type == "unknown")

        mc1, mc2 = st.columns(2)
        mc1.metric("✅ Present Today", len(present_today))
        mc2.metric("❓ Unknown", unk_count)
        mc3, mc4 = st.columns(2)
        mc3.metric("⚠️ Expired", len(expired_mems))
        mc4.metric("👤 Enrolled", len(enrolled))

        st.divider()
        if enrolled:
            st.caption(
                f"✅ **{len(enrolled)}** enrolled · threshold **{FACE_THRESHOLD}**  \n"
                f"🖼️ Captures (3-day auto-del): **{len(captures_db)}**"
            )
        else:
            st.warning("⚠️ 0 faces enrolled  \nMembers page par photo upload karein")

        if present_today:
            st.markdown("**⚡ Recent:**")
            mmap = {m.id: m for m in all_members}
            for rec in reversed(present_today[-5:]):
                mm = mmap.get(rec.member_id)
                if not mm:
                    continue
                t = rec.created_at.strftime("%H:%M") if rec.created_at else "—"
                st.markdown(
                    f"<div style='padding:.2rem 0;border-bottom:1px solid #1E293B;'>"
                    f"✅ <b>{mm.full_name}</b>"
                    f"<span style='color:#94A3B8;font-size:.78rem;float:right'>·{t}</span></div>",
                    unsafe_allow_html=True,
                )

    # ── Bottom tabs ───────────────────────────────────────────────────────────
    st.divider()
    mmap_full  = {m.id: m for m in all_members}
    tab_labels = ["✅ Present Today", "⚠️ Expired Members"]
    if role in ("admin", "auditor"):
        tab_labels.append("📸 Captures (Admin)")
    btabs = st.tabs(tab_labels)

    with btabs[0]:
        present_today2 = [r for r in db.get_attendance(gym_id=face_gym_id,
                                                         check_date=date.today())
                          if r.status == "Present"]
        if not present_today2:
            st.info("Abhi koi face attendance nahi hua aaj.")
        else:
            for rec in reversed(present_today2[-60:]):
                mm = mmap_full.get(rec.member_id)
                if not mm:
                    continue
                c1, c2 = st.columns([1, 4])
                with c1:
                    show_member_photo(mm.photo_path, width=60)
                with c2:
                    t = rec.created_at.strftime("%H:%M") if rec.created_at else "—"
                    st.markdown(
                        f"**{mm.full_name}** ✅  \n"
                        f"<span style='color:#94A3B8;font-size:.82rem;'>"
                        f"{mm.serial_number} · {t}</span>",
                        unsafe_allow_html=True,
                    )
                st.divider()

    with btabs[1]:
        if not expired_mems:
            st.success("✅ Koi expired member nahi hai.")
        else:
            st.error(f"⚠️ {len(expired_mems)} members expired!")
            for mm in expired_mems:
                e1, e2 = st.columns([1, 4])
                with e1:
                    show_member_photo(mm.photo_path, width=60)
                with e2:
                    try:
                        d_ago = (date.today() - date.fromisoformat(mm.expiry_date)).days
                    except Exception:
                        d_ago = "?"
                    st.markdown(
                        f"**{mm.full_name}**  \n"
                        f"<span style='color:#FCA5A5;font-size:.85rem;'>"
                        f"Expired: {mm.expiry_date} ({d_ago}d ago) · {mm.serial_number}</span>",
                        unsafe_allow_html=True,
                    )
                st.divider()

    if role in ("admin", "auditor") and len(btabs) > 2:
        with btabs[2]:
            all_caps = db.get_unknown_captures(gym_id=face_gym_id, limit=100)
            st.caption("🗑️ Captures 3 din baad auto-delete ho jayenge.")
            if not all_caps:
                st.success("✅ Koi capture nahi hai.")
            else:
                for cap in all_caps:
                    c1, c2, c3 = st.columns([1, 3, 1])
                    with c1:
                        img_b = object_store.get_capture_bytes(cap.capture_key)
                        if img_b:
                            st.image(io.BytesIO(img_b), width=75)
                        else:
                            st.markdown("🖼️")
                    with c2:
                        badge = "❓ UNKNOWN" if cap.capture_type == "unknown" else "⚠️ EXPIRED"
                        nm    = cap.member_name or "Unknown"
                        ts    = (cap.captured_at.strftime("%d %b %H:%M")
                                 if cap.captured_at else "—")
                        st.markdown(
                            f"**{badge}** — {nm}  \n"
                            f"<span style='color:#94A3B8;font-size:.8rem;'>{ts}</span>",
                            unsafe_allow_html=True,
                        )
                    with c3:
                        if st.button("🗑️", key=f"dc_{cap.id}", help="Delete"):
                            object_store.delete_capture(cap.capture_key)
                            db.delete_unknown_capture_record(cap.id)
                            st.toast("Deleted", icon="🗑️")
                    st.divider()

                if st.button("🗑️ Delete All", key="del_all_caps",
                             type="secondary", use_container_width=True):
                    for cap in all_caps:
                        object_store.delete_capture(cap.capture_key)
                        db.delete_unknown_capture_record(cap.id)
                    st.success("✅ Sab delete.")


# ── Main tab entry ────────────────────────────────────────────────────────────
def render_face_recognition_tab(gym_id, role, current_user, gyms):
    _face_ss_init()
    _run_cleanup()

    gym_opts    = {g.name: g.id for g in gyms}
    face_gym_id = gym_id
    if not gym_id:
        chosen      = st.selectbox("Gym select karein",
                                   list(gym_opts.keys()), key="face_gym_sel")
        face_gym_id = gym_opts[chosen]
    else:
        st.caption(f"📍 **{next((g.name for g in gyms if g.id == gym_id), '')}**")

    # Auto-generate encodings from profile photos (retries every call if count=0)
    with st.spinner("🔄 Face encodings check kar rahe hain..."):
        newly = _auto_generate_encodings(face_gym_id)
    if newly:
        st.toast(f"✅ {newly} member(s) ke face auto-register ho gaye!", icon="🎉")
    else:
        enc_count = len(db.get_face_encodings(face_gym_id))
        if enc_count == 0:
            st.warning(
                "⚠️ **Koi face encoding nahi hai.**  \n"
                "Members page par members ke photos upload karein — "
                "yeh system automatically unke faces register kar lega."
            )
        else:
            st.caption(f"✅ {enc_count} member faces ready · Threshold: {FACE_THRESHOLD}")

    _face_camera_fragment(face_gym_id, current_user, role, gyms)


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role, current_user):
    init_session_state()
    
    styles.page_header("📅", "Daily Attendance Controls",
                       "Scan a member's QR code or monitor live AI security logs")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_scan, tab_manual, tab_face, tab_view = st.tabs(
        ["🎯 QR Scan & Main Dashboard AI", "✅ Mark Manually", "📸 Face Check-in", "📊 View Records"]
    )

    # ── QR Scan & Main Dashboard Intel Tab ───────────────────────────────────
    with tab_scan:
        st.components.v1.html(_AUDIO_PRIMER_JS, height=0)
        gym_opts = {g.name: g.id for g in gyms}
        if gym_id:
            sel_gid = gym_id
            gname = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
            st.caption(f"📍 Scanning at: **{gname}** · {date.today().isoformat()}")
        else:
            chosen = st.selectbox("Select gym (kiosk location)",
                                  list(gym_opts.keys()), key="qr_scan_gym")
            sel_gid = gym_opts[chosen]
            st.caption(f"📍 {date.today().isoformat()}")

        last = st.session_state.get("qr_last_result")
        if last:
            if last["kind"] == "success":
                _big_banner("#064E3B", "#10B981",
                            f'{last["headline"]} · {last["sub"]}',
                            icon="✅")
                _play("beep")
                m = last.get("member")
                if m:
                    show_member_photo(m.photo_path, width=160)
                if m:
                    st.caption(
                        f"Serial **{m.serial_number}** · "
                        f"{m.membership_type} · expires {m.expiry_date or '—'}"
                    )
            elif last["kind"] == "expired":
                _big_banner("#7F1D1D", "#EF4444",
                            "⚠️ FEES EXPIRED — PLEASE PAY AT COUNTER",
                            last["sub"], icon="🚫")
                _play("buzz")
                m = last.get("member")
                if m:
                    show_member_photo(m.photo_path, width=160)
            else:
                _big_banner("#7F1D1D", "#EF4444",
                            last["headline"], last["sub"], icon="❌")
                _play("buzz")

        with st.form("qr_scan_form", clear_on_submit=True):
            st.text_input(
                "Scan member QR code",
                key="qr_scan_input",
                placeholder="Scan now — or type a serial and press Enter",
                autocomplete="off",
                help="USB scanner emits the code + Enter. Field auto-focuses.",
            )
            submitted = st.form_submit_button("✓ Check In", type="primary",
                                              use_container_width=True)
        if submitted:
            raw = st.session_state.get("qr_scan_input", "")
            st.session_state["qr_last_result"] = _process_scan(
                raw, sel_gid, current_user)
            st.rerun()

        _autofocus_scan_input()
        st.divider()
        render_ai_dashboard_intel(sel_gid)

        recent = db.get_recent_scans(gym_id=sel_gid, limit=100, today_only=True)

        st.markdown("##### 🟢 Inside Gym Right Now (Active 2-Hour Window)")
        inside_now = []
        now = datetime.now()

        if recent:
            for r in recent:
                try:
                    r_time = datetime.strptime(r["time"], "%H:%M").time()
                    r_datetime = datetime.combine(date.today(), r_time)
                    if now - r_datetime < timedelta(hours=2) and r_datetime <= now:
                        inside_now.append(r)
                except Exception:
                    inside_now.append(r)

        st.metric(label="Live Counter Status", value=f"{len(inside_now)} Members Inside")

        if not inside_now:
            st.info("No members inside the gym right now based on recent check-ins.")
        else:
            df_live = pd.DataFrame([
                {"⚡ In-Time": r["time"], "Serial ID": r["serial"], "Member Name": r["name"]}
                for r in inside_now
            ])
            st.dataframe(df_live, use_container_width=True, hide_index=True)

        st.write("") 

        st.markdown("##### 📋 Today's Full Attendance History")
        if not recent:
            st.caption("No check-ins yet today.")
        else:
            df_all = pd.DataFrame([
                {"Time": r["time"], "Serial": r["serial"], "Name": r["name"],
                 "Marked By": r["marked_by"]}
                for r in recent
            ])
            st.dataframe(df_all, use_container_width=True, hide_index=True,
                         height=min(200, 50 + 35 * len(recent)))

    # ── Mark Manually ────────────────────────────────────────────────────────
    with tab_manual:
        c1, c2, c3 = st.columns(3)

        with c1:
            if gym_id:
                gname = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
                st.text_input("Gym", value=gname, disabled=True, key="att_gym_display")
                sel_gid = gym_id
            else:
                chosen = st.selectbox("Gym", list(gym_opts.keys()), key="att_gym")
                sel_gid = gym_opts[chosen]

        with c2:
            att_date = st.date_input("Attendance Date", value=date.today(), key="att_date")

        with c3:
            st.write("")
            st.write("")
            if st.button("🔄 Reset Today's Marks", use_container_width=True,
                         help="Aaj ke marked members ko dobara list mein laayein"):
                st.session_state.pop(f"marked_today_{sel_gid}_{att_date}", None)
                st.rerun()

        all_active_members = db.get_members(gym_id=sel_gid, status="Active")
        existing = {a.member_id: a.status for a in
                    db.get_attendance(gym_id=sel_gid, check_date=att_date)}

        session_key = f"marked_today_{sel_gid}_{att_date}"
        if session_key not in st.session_state:
            st.session_state[session_key] = set(existing.keys())

        marked_ids = st.session_state[session_key]
        pending_members = [m for m in all_active_members if m.id not in marked_ids]
        marked_members = [m for m in all_active_members if m.id in marked_ids]

        s1, s2, s3, s4 = st.columns(4)
        total = len(all_active_members)
        done = len(marked_members)
        remaining = len(pending_members)
        progress = (done / total * 100) if total > 0 else 0

        with s1:
            st.markdown(styles.metric_card("Total Active", total,
                                           "Members", "purple"), unsafe_allow_html=True)
        with s2:
            st.markdown(styles.metric_card("✅ Marked", done,
                                           f"{progress:.0f}% done", "green"), unsafe_allow_html=True)
        with s3:
            st.markdown(styles.metric_card("⏳ Pending", remaining,
                                           "Abhi baqi hain", "amber"), unsafe_allow_html=True)
        with s4:
            present_count = sum(1 for mid, s in existing.items() if s == "Present")
            st.markdown(styles.metric_card("🟢 Present", present_count,
                                           "Aaj aaye", "blue"), unsafe_allow_html=True)

        if total > 0:
            st.progress(done / total, text=f"Progress: {done}/{total} members marked")

        st.divider()

        search_col, info_col = st.columns([2, 1])
        with search_col:
            search_q = st.text_input("🔍 Search member",
                                     placeholder="Name ya Serial number...",
                                     key="manual_att_search",
                                     label_visibility="collapsed")
        with info_col:
            st.caption("💡 Mark karte jayein — naam list se hat jayega")

        if search_q:
            q = search_q.lower()
            pending_members = [m for m in pending_members
                               if q in m.full_name.lower()
                               or q in (m.serial_number or "").lower()]

        st.markdown(f"### 📋 Pending Members ({len(pending_members)})")

        if not pending_members:
            if remaining == 0:
                st.success("🎉 Sab members ki attendance mark ho gayi hai! Shabash!")
            else:
                st.info("Search se koi member match nahi hua.")
        else:
            for m in pending_members:
                with st.container():
                    col_pic, col_info, col_p, col_a, col_l = st.columns([1.2, 3, 1.2, 1.2, 1.2])

                    with col_pic:
                        show_member_photo(m.photo_path, width=90)

                    with col_info:
                        st.markdown(
                            f"""
                            <div style="padding-top:12px;">
                                <div style="font-size:1.2rem; font-weight:700; color:#F8FAFC;">
                                    {m.full_name}
                                </div>
                                <div style="font-size:0.9rem; color:#94A3B8;">
                                    🆔 {m.serial_number} · {m.membership_type or 'N/A'}
                                </div>
                                <div style="font-size:0.85rem; color:#64748B;">
                                    📞 {m.phone or '—'}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col_p:
                        st.write("")
                        if st.button("✅ Present", key=f"p_{m.id}",
                                     use_container_width=True, type="primary"):
                            ok, msg = db.mark_attendance(m.id, sel_gid, att_date,
                                                         "Present", current_user)
                            if ok:
                                st.session_state[session_key].add(m.id)
                                st.toast(f"✅ {m.full_name} marked Present", icon="✅")
                                st.rerun()
                            else:
                                st.error(msg)

                    with col_a:
                        st.write("")
                        if st.button("❌ Absent", key=f"a_{m.id}",
                                     use_container_width=True):
                            ok, msg = db.mark_attendance(m.id, sel_gid, att_date,
                                                         "Absent", current_user)
                            if ok:
                                st.session_state[session_key].add(m.id)
                                st.toast(f"❌ {m.full_name} marked Absent", icon="❌")
                                st.rerun()
                            else:
                                st.error(msg)

                    with col_l:
                        st.write("")
                        if st.button("🕐 Late", key=f"l_{m.id}",
                                     use_container_width=True):
                            ok, msg = db.mark_attendance(m.id, sel_gid, att_date,
                                                         "Late", current_user)
                            if ok:
                                st.session_state[session_key].add(m.id)
                                st.toast(f"🕐 {m.full_name} marked Late", icon="🕐")
                                st.rerun()
                            else:
                                st.error(msg)

                    st.markdown(
                        "<hr style='margin:0.5rem 0; border-color:#1E293B;'>",
                        unsafe_allow_html=True
                    )

        if marked_members:
            st.divider()
            with st.expander(f"✅ Already Marked Today ({len(marked_members)}) — Click to view"):
                marked_rows = []
                for m in marked_members:
                    status = existing.get(m.id, "—")
                    status_emoji = {
                        "Present": "✅ Present",
                        "Absent": "❌ Absent",
                        "Late": "🕐 Late",
                        "Excused": "📝 Excused"
                    }.get(status, status)

                    marked_rows.append({
                        "Serial": m.serial_number,
                        "Name": m.full_name,
                        "Status": status_emoji,
                        "Type": m.membership_type or "—",
                    })

                st.dataframe(pd.DataFrame(marked_rows),
                             use_container_width=True, hide_index=True)

                st.caption("💡 Galti se mark kiya? Upar **'🔄 Reset Today's Marks'** button dabayein.")

    # ========== TAB 3: FACE RECOGNITION ==========
    with tab_face:
        render_face_recognition_tab(gym_id, role, current_user, gyms)

    # ── View Records ──────────────────────────────────────────────────────────
    with tab_view:
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            if gym_id:
                vgid = gym_id
                st.text_input("Gym",
                              value=next((g.name for g in gyms if g.id == gym_id), ""),
                              disabled=True, key="vatt_gym_display")
            else:
                chosen2 = st.selectbox("Gym", list(gym_opts.keys()),
                                       key="vatt_gym")
                vgid = gym_opts[chosen2]
        with vc2:
            vdate = st.date_input("Date", value=date.today(), key="vatt_date")
        with vc3:
            st.write("")
            st.write("")
            if st.button("🔄 Fix Photo Orientations", use_container_width=True,
                        help="Clear photo cache and reload with correct orientation"):
                st.session_state.attendance_photo_cache = {}
                st.success("✅ Photo cache cleared! Images will reload with correct orientation.")
                st.rerun()

        records = db.get_attendance(gym_id=vgid, check_date=vdate)
        members_map = {m.id: m for m in db.get_members(gym_id=vgid)}
        if records:
            rows = []
            present = 0
            for r in records:
                m = members_map.get(r.member_id)
                if r.status == "Present":
                    present += 1
                rows.append({
                    "Serial": m.serial_number if m else "—",
                    "Name": m.full_name if m else "—",
                    "Status": r.status,
                    "Marked By": r.marked_by or "—",
                    "Time": r.created_at.strftime("%H:%M") if r.created_at else "—",
                })
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total Marked", len(records))
            mc2.metric("Present", present)
            mc3.metric("Absent / Other", len(records) - present)
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True)
        else:
            st.info(f"No attendance records for {vdate}.")