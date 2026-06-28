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
# SESSION STATE INITIALIZATION (FIXED)
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
    # Ensure session state is initialized
    init_session_state()
    
    if photo_field:
        # Try to get compressed photo with orientation fix
        photo_b64 = get_attendance_photo_b64(photo_field, "")
        if photo_b64:
            # SQUARE FRAME with bigger size
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
        
        # Fallback: try direct path
        path = get_photo_path(photo_field)
        if path:
            try:
                # Compress and fix orientation on the fly
                compressed = compress_image_with_orientation(path)
                if compressed:
                    b64 = base64.b64encode(compressed).decode()
                    # SQUARE FRAME with bigger size
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
    
    # Default placeholder - SQUARE
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

# ── Audio (Web Audio API tone ── no external files needed) ────────────────────
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

_BEEP_JS = _tone_js(880, 180, "sine",   0.18)
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
    
    from datetime import date
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


_AUTO_CLICK_JS = """
<script>
(function(){
  var _faceInterval = null;
  function clickCamBtn() {
    var doc = window.parent ? window.parent.document : document;
    var btns = doc.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      var t = btns[i].innerText.trim().toLowerCase();
      if (t === 'take photo' || t === '📷' || t.includes('take photo')) {
        btns[i].click();
        return;
      }
    }
  }
  clearInterval(_faceInterval);
  _faceInterval = setInterval(clickCamBtn, 3500);
  setTimeout(clickCamBtn, 1800);
})();
</script>
"""

_FACE_TAB_SS_DEFAULTS = {
    "face_auto_mode": False,
    "face_unknown_log": [],       # list of {time, snapshot_b64}
    "face_today_marked": set(),   # member ids marked via face today
    "face_last_result": None,     # dict with last detection info
    "face_enc_cache": None,       # cached encodings list
    "face_enc_cache_gym": None,   # gym_id for the cached encodings
    "face_enroll_member_id": None,
}

def _face_ss_init():
    for k, v in _FACE_TAB_SS_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v if not callable(v) else v()


def _load_encodings(gym_id):
    """Load and cache face encodings for the selected gym."""
    if (st.session_state.face_enc_cache is None
            or st.session_state.face_enc_cache_gym != gym_id):
        st.session_state.face_enc_cache = db.get_face_encodings(gym_id)
        st.session_state.face_enc_cache_gym = gym_id
    return st.session_state.face_enc_cache


def _match_face(encoding, encodings_list) -> dict | None:
    """Find best matching member. Returns member dict or None."""
    best_score = 0.0
    best = None
    for m in encodings_list:
        stored = face_engine.str_to_encoding(m["encoding_json"])
        if stored is None:
            continue
        score = face_engine.similarity(encoding, stored)
        if score > best_score:
            best_score = score
            best = m
    if best and best_score >= face_engine.SIMILARITY_THRESHOLD:
        return {**best, "score": best_score}
    return None


def _result_banner(kind: str, name: str = "", detail: str = ""):
    colors = {
        "success": ("#064E3B", "#10B981"),
        "expired": ("#78350F", "#F59E0B"),
        "unknown": ("#1E1B4B", "#6366F1"),
        "error":   ("#1E1B4B", "#EF4444"),
    }
    icons = {"success": "✅", "expired": "⚠️", "unknown": "❓", "error": "🚫"}
    bg, border = colors.get(kind, ("#1E293B", "#475569"))
    icon = icons.get(kind, "ℹ️")
    st.markdown(
        f"""
        <div style="background:{bg};border:3px solid {border};border-radius:16px;
                    padding:1.2rem 1rem;text-align:center;margin:0.6rem 0;">
          <div style="font-size:2.8rem;line-height:1;">{icon}</div>
          <div style="font-size:1.6rem;font-weight:900;color:#fff;margin-top:.3rem;">{name}</div>
          <div style="font-size:.9rem;color:#CBD5E1;margin-top:.3rem;">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _process_face_image(pil_img, gym_id, current_user):
    """
    Detect face → match → mark attendance.
    Returns result dict with keys: kind, name, detail, member (optional).
    """
    img_bgr = face_engine.pil_to_bgr(pil_img)
    encoding = face_engine.get_encoding(img_bgr)

    if encoding is None:
        return {"kind": "error", "name": "NO FACE DETECTED",
                "detail": "Camera ke saamne aayein — seedha / clear light mein"}

    encodings = _load_encodings(gym_id)
    if not encodings:
        return {"kind": "error", "name": "NO FACES ENROLLED",
                "detail": "Pehle members ke faces enroll karein (neeche ↓)"}

    match = _match_face(encoding, encodings)

    if match is None:
        snap_b64 = base64.b64encode(pil_img.resize((160, 160)).tobytes()).decode()
        entry = {"time": datetime.now().strftime("%H:%M:%S"), "snap": snap_b64}
        st.session_state.face_unknown_log.append(entry)
        return {"kind": "unknown", "name": "UNKNOWN PERSON",
                "detail": "Is shaks ki face enrollment nahi hai ya match nahi hua"}

    member_id = match["id"]
    status = (match["status"] or "active").lower()

    # Expired check
    if match["expiry_date"]:
        try:
            exp = date.fromisoformat(match["expiry_date"])
            if exp < date.today():
                return {"kind": "expired", "name": match["full_name"],
                        "detail": f"Membership expired {match['expiry_date']} — please pay at counter",
                        "member": match}
        except Exception:
            pass

    # Inactive check
    if status not in ("active",):
        return {"kind": "error", "name": match["full_name"],
                "detail": f"Account {match['status']} — please see counter",
                "member": match}

    # Mark attendance
    ok, msg = db.mark_attendance(member_id, match["gym_id"],
                                  date.today(), "Present", current_user)
    st.session_state.face_today_marked.add(member_id)
    # Invalidate encoding cache so fresh list is shown
    st.session_state.face_enc_cache = None

    score_pct = f"{match['score']*100:.0f}%"
    return {
        "kind": "success",
        "name": f"WELCOME  {match['full_name']}",
        "detail": f"✅ Attendance marked · Match {score_pct} · {match['serial_number']}",
        "member": match,
    }


def render_face_recognition_tab(gym_id, role, current_user, gyms):
    _face_ss_init()

    gym_opts = {g.name: g.id for g in gyms}

    # ── Controls row ─────────────────────────────────────────────────────────
    ctrl_l, ctrl_r = st.columns([3, 1])
    with ctrl_l:
        if gym_id:
            face_gym_id = gym_id
            st.caption(f"📍 Gym: **{next((g.name for g in gyms if g.id==gym_id), '')}**")
        else:
            chosen = st.selectbox("Select Gym", list(gym_opts.keys()),
                                  key="face_gym_sel")
            face_gym_id = gym_opts[chosen]
    with ctrl_r:
        auto = st.toggle("⚡ Auto Mode",
                         value=st.session_state.face_auto_mode,
                         key="face_auto_toggle",
                         help="Auto-clicks camera every 3.5 seconds")
        st.session_state.face_auto_mode = auto

    if auto:
        st.components.v1.html(_AUTO_CLICK_JS, height=0)
        st.info("⚡ Auto Mode ON — camera is capturing every 3–4 seconds")

    # ── Main 2-column layout ──────────────────────────────────────────────────
    cam_col, stat_col = st.columns([6, 4], gap="medium")

    with cam_col:
        st.markdown("##### 📷 Live Camera Feed")
        cam_img = st.camera_input(
            "Camera",
            key=f"face_cam_{int(time.time()//8)}",
            label_visibility="collapsed",
        )

        if cam_img is not None:
            pil = Image.open(cam_img)
            with st.spinner("🔍 Recognizing..."):
                result = _process_face_image(pil, face_gym_id, current_user)
            st.session_state.face_last_result = result

            # Annotate image
            img_bgr = face_engine.pil_to_bgr(pil)
            color_map = {"success":(0,220,100), "expired":(0,180,255),
                         "unknown":(200,60,220), "error":(60,60,255)}
            color = color_map.get(result["kind"], (200,200,200))
            label = result["name"][:20]
            annotated = face_engine.annotate(img_bgr, label, color)
            ann_pil = Image.fromarray(
                __import__("cv2").cvtColor(annotated, __import__("cv2").COLOR_BGR2RGB)
            )
            st.image(ann_pil, use_container_width=True)

            _result_banner(result["kind"], result["name"], result["detail"])

            # Beep sounds
            if result["kind"] == "success":
                st.components.v1.html(_BEEP_JS, height=0)
            elif result["kind"] in ("expired", "unknown"):
                st.components.v1.html(_BUZZ_JS, height=0)
        else:
            # No capture yet — show last result if any
            lr = st.session_state.face_last_result
            if lr:
                _result_banner(lr["kind"], lr["name"], lr["detail"])
            else:
                st.markdown(
                    """<div style="background:#0F172A;border:2px dashed #334155;
                                  border-radius:12px;padding:2rem;text-align:center;
                                  color:#64748B;font-size:1rem;">
                    📷 Camera band hai — upar "Take photo" dabayein<br>
                    ya Auto Mode ON karein
                    </div>""",
                    unsafe_allow_html=True,
                )

    with stat_col:
        st.markdown("##### 📊 Today's Summary")
        enrolled = db.get_face_encodings(face_gym_id)
        all_today_att = db.get_attendance(gym_id=face_gym_id, check_date=date.today())
        present_today = [r for r in all_today_att if r.status == "Present"]
        unknown_count = len(st.session_state.face_unknown_log)
        all_members  = db.get_members(gym_id=face_gym_id)
        expired_list = [
            m for m in all_members
            if m.expiry_date and date.fromisoformat(m.expiry_date) < date.today()
        ]

        m1, m2 = st.columns(2)
        m1.metric("✅ Present", len(present_today))
        m2.metric("❓ Unknown", unknown_count)
        m3, m4 = st.columns(2)
        m3.metric("⚠️ Expired", len(expired_list))
        m4.metric("👤 Enrolled", len(enrolled))

        st.divider()

        # ── Face Enrollment ────────────────────────────────────────────────
        with st.expander("👤 Face Enrollment", expanded=len(enrolled) == 0):
            st.caption("Pehli baar: har member ka face enroll karein")
            members = db.get_members(gym_id=face_gym_id, status="Active")
            if not members:
                st.info("Koi Active member nahi mila.")
            else:
                enrolled_ids = {e["id"] for e in enrolled}
                search_e = st.text_input("Search", placeholder="Name ya serial...",
                                         key="face_enroll_search", label_visibility="collapsed")
                if search_e:
                    q = search_e.lower()
                    members = [m for m in members
                               if q in m.full_name.lower()
                               or q in (m.serial_number or "").lower()]

                for m in members[:20]:
                    tag = "✅ Enrolled" if m.id in enrolled_ids else "⬜ Not enrolled"
                    with st.container():
                        ec1, ec2 = st.columns([3, 2])
                        with ec1:
                            st.markdown(
                                f"**{m.full_name}**  \n"
                                f"<span style='color:#94A3B8;font-size:.8rem;'>"
                                f"{m.serial_number} · {tag}</span>",
                                unsafe_allow_html=True,
                            )
                        with ec2:
                            if st.button("📷 Enroll",
                                         key=f"enroll_{m.id}",
                                         use_container_width=True):
                                st.session_state.face_enroll_member_id = m.id
                                st.rerun()

                # If enrollment capture active
                enroll_id = st.session_state.face_enroll_member_id
                if enroll_id:
                    em = next((m for m in members if m.id == enroll_id), None)
                    if em:
                        st.info(f"📷 **{em.full_name}** ka face enroll kar rahe hain")
                        enroll_photo = st.camera_input(
                            f"Enroll: {em.full_name}",
                            key=f"enroll_cam_{enroll_id}",
                        )
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if enroll_photo and st.button("💾 Save Face",
                                                           key="enroll_save",
                                                           type="primary",
                                                           use_container_width=True):
                                pil = Image.open(enroll_photo)
                                enc = face_engine.get_encoding_from_pil(pil)
                                if enc is None:
                                    st.error("❌ No face detected — seedha camera ke saamne aayein")
                                else:
                                    ok, msg = db.save_face_encoding(
                                        enroll_id, face_engine.encoding_to_str(enc)
                                    )
                                    if ok:
                                        st.success(f"✅ {em.full_name} enrolled!")
                                        st.session_state.face_enroll_member_id = None
                                        st.session_state.face_enc_cache = None
                                        st.rerun()
                                    else:
                                        st.error(f"DB error: {msg}")
                        with col_cancel:
                            if st.button("❌ Cancel", key="enroll_cancel",
                                         use_container_width=True):
                                st.session_state.face_enroll_member_id = None
                                st.rerun()

    # ── Bottom tabs ───────────────────────────────────────────────────────────
    st.divider()
    bt1, bt2, bt3 = st.tabs(["✅ Attendance Today", "❓ Unknown Log", "⚠️ Expired List"])

    members_map = {m.id: m for m in db.get_members(gym_id=face_gym_id)}

    with bt1:
        if not present_today:
            st.info("Abhi koi face attendance nahi hua aaj.")
        else:
            for rec in reversed(present_today[-50:]):
                m = members_map.get(rec.member_id)
                if not m:
                    continue
                rc1, rc2, rc3 = st.columns([1, 3, 1])
                with rc1:
                    show_member_photo(m.photo_path, width=70)
                with rc2:
                    t = rec.created_at.strftime("%H:%M") if rec.created_at else "—"
                    st.markdown(
                        f"**{m.full_name}**  \n"
                        f"<span style='color:#94A3B8;font-size:.85rem;'>"
                        f"{m.serial_number} · {t}</span>",
                        unsafe_allow_html=True,
                    )
                with rc3:
                    st.markdown("✅ Present", unsafe_allow_html=True)
                st.divider()

    with bt2:
        unknowns = st.session_state.face_unknown_log
        if not unknowns:
            st.success("✅ Aaj koi unknown person nahi aya.")
        else:
            st.warning(f"⚠️ {len(unknowns)} unknown person(s) detected today (is session mein)")
            for i, u in enumerate(reversed(unknowns[-30:])):
                st.markdown(
                    f"<div style='background:#1E1B4B;border:1px solid #4338CA;"
                    f"border-radius:8px;padding:.6rem .8rem;margin:.3rem 0;"
                    f"color:#E0E7FF;'>❓ Unknown visitor — {u['time']}</div>",
                    unsafe_allow_html=True,
                )
            if st.button("🗑️ Clear Log", key="clear_unknown_log"):
                st.session_state.face_unknown_log = []
                st.rerun()

    with bt3:
        if not expired_list:
            st.success("✅ Koi expired member nahi hai.")
        else:
            st.error(f"⚠️ {len(expired_list)} members ki membership expire ho chuki hai!")
            for m in expired_list:
                ec1, ec2, ec3 = st.columns([1, 3, 1])
                with ec1:
                    show_member_photo(m.photo_path, width=70)
                with ec2:
                    st.markdown(
                        f"**{m.full_name}**  \n"
                        f"<span style='color:#FCA5A5;font-size:.85rem;'>"
                        f"Expired: {m.expiry_date} · {m.serial_number}</span>",
                        unsafe_allow_html=True,
                    )
                with ec3:
                    days_ago = (date.today() - date.fromisoformat(m.expiry_date)).days
                    st.markdown(
                        f"<span style='color:#FCA5A5;font-size:.8rem;'>"
                        f"{days_ago}d ago</span>",
                        unsafe_allow_html=True,
                    )
                st.divider()

    # Auto-mode rerun loop
    if st.session_state.face_auto_mode:
        time.sleep(3)
        st.rerun()

# ── Page ─────────────────────────────────────────────────────────────────────
def render(gym_id, role, current_user):
    # Ensure session state is initialized
    init_session_state()
    
    styles.page_header("📅", "Daily Attendance Controls",
                       "Scan a member's QR code or monitor live AI security logs")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # 4 TABS - including Face Check-in
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

    # ── Mark Manually (Picture + 3 Buttons + Auto-Remove) ───────────────────
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
                    "Name":   m.full_name if m else "—",
                    "Status": r.status,
                    "Marked By": r.marked_by or "—",
                    "Time":  r.created_at.strftime("%H:%M") if r.created_at else "—",
                })
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total Marked", len(records))
            mc2.metric("Present", present)
            mc3.metric("Absent / Other", len(records) - present)
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True)
        else:
            st.info(f"No attendance records for {vdate}.")