import streamlit as st
import os
import base64
import json
import io
import time
import qrcode
from datetime import date, datetime, timedelta
import pandas as pd
import object_store
import face_engine
from PIL import Image

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False

import database as db
import styles

UPLOAD_DIR = "gym-app/uploads"

# ════════════════════════════════════════════════════════════════════════════
# FAST CACHED FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def _cached_gym_members(gym_id, status="Active"):
    return db.get_members(gym_id=gym_id, status=status)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_today_attendance(gym_id):
    return db.get_attendance(gym_id=gym_id, check_date=date.today())

@st.cache_data(ttl=300, show_spinner=False)
def _cached_attendance_trend(gym_id, days=30):
    return db.get_attendance_trend(gym_id=gym_id, days=days)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_absent_members(gym_id, days=3):
    return db.get_absent_members(days=days, gym_id=gym_id)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_leaderboard(gym_id, limit=10):
    return db.get_attendance_leaderboard(gym_id=gym_id, limit=limit)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_attendance_by_hour(gym_id):
    return db.get_attendance_by_hour(gym_id=gym_id)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_recent_scans(gym_id, limit=100):
    return db.get_recent_scans(gym_id=gym_id, limit=limit, today_only=True)

@st.cache_data(ttl=3600, show_spinner=False)
def _cached_photo_b64(photo_field: str, serial_number: str = ""):
    if not photo_field:
        return None
    for key in filter(None, [photo_field, f"member_photos/{serial_number}.jpg" if serial_number else None]):
        try:
            b64, _ = object_store.get_photo_b64(key)
            if b64:
                return f"data:image/jpeg;base64,{b64}"
        except Exception:
            pass
    return None

# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════════════════

def init_session_state():
    defaults = {
        'attendance_photo_cache': {},
        'face_enabled': False,
        'face_last_result': None,
        'face_enc_cache': None,
        'face_enc_cache_ts': 0.0,
        'face_enc_cache_gym': None,
        'face_cam_gen': 0,
        'qr_last_result': None,
        'page_num': 1,
        'staff_checkin_status': {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ════════════════════════════════════════════════════════════════════════════
# PHOTO HELPERS
# ════════════════════════════════════════════════════════════════════════════

def get_attendance_photo_b64(photo_field: str, serial_number: str = "") -> str | None:
    cache_key = f"attendance_{serial_number}_{photo_field}"
    if cache_key in st.session_state.attendance_photo_cache:
        return st.session_state.attendance_photo_cache[cache_key]
    
    result = _cached_photo_b64(photo_field, serial_number)
    if result:
        st.session_state.attendance_photo_cache[cache_key] = result
    return result

def show_member_photo(photo_field, width=100):
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

# ════════════════════════════════════════════════════════════════════════════
# AUDIO & SCAN HELPERS
# ════════════════════════════════════════════════════════════════════════════

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
        return {"kind": "error", "headline": "EMPTY SCAN", "sub": "No code received."}

    member = db.get_member_by_serial(serial, gym_id=gym_id)
    if not member:
        global_match = db.get_member_by_serial(serial)
        if global_match:
            return {
                "kind": "error",
                "headline": "WRONG GYM",
                "sub": f"{global_match.full_name} ({serial}) belongs to a different gym.",
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
                    "sub": f"PLEASE PAY AT COUNTER · {member.full_name} · expired {member.expiry_date}",
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

# ════════════════════════════════════════════════════════════════════════════
# FACE RECOGNITION
# ════════════════════════════════════════════════════════════════════════════

_ENC_CACHE_TTL = 300
_MEMBER_COOLDOWN = 60
_CAP_RATE_LIMIT = 10
FACE_THRESHOLD = 0.40

def _face_ss_init():
    defs = {
        "face_last_result": None,
        "face_enc_cache": None,
        "face_enc_cache_ts": 0.0,
        "face_enc_cache_gym": None,
        "face_cam_gen": 0,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _load_encodings(gym_id):
    now = time.time()
    stale = (
        st.session_state.face_enc_cache is None
        or st.session_state.face_enc_cache_gym != gym_id
        or now - st.session_state.face_enc_cache_ts > _ENC_CACHE_TTL
    )
    if stale:
        st.session_state.face_enc_cache = db.get_face_encodings(gym_id)
        st.session_state.face_enc_cache_gym = gym_id
        st.session_state.face_enc_cache_ts = now
    return st.session_state.face_enc_cache

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

def _process_face_image(pil_img, gym_id, current_user):
    w, h = pil_img.size
    if w > 320:
        pil_img = pil_img.resize((320, int(h * 320 / w)), Image.BILINEAR)

    img_bgr = face_engine.pil_to_bgr(pil_img)
    faces = face_engine.detect_faces(img_bgr)
    if not faces:
        return {"kind": "noface", "name": "Koi face nahi mila",
                "detail": "Camera ke bilkul saamne aayein"}

    encoding = face_engine.get_encoding(img_bgr)
    if encoding is None:
        return {"kind": "noface", "name": "Encoding fail",
                "detail": "Thora aur qareeb aayein"}

    encodings = _load_encodings(gym_id)
    if not encodings:
        return {"kind": "error", "name": "KOI PHOTO REGISTERED NAHI",
                "detail": "Members page par photo upload karein"}

    match = _match_face(encoding, encodings)
    if match is None:
        return {"kind": "unknown", "name": "UNKNOWN PERSON",
                "detail": f"Match nahi hua (threshold: {FACE_THRESHOLD})"}

    if match.get("expiry_date"):
        try:
            if date.fromisoformat(match["expiry_date"]) < date.today():
                return {
                    "kind": "expired", "name": match["full_name"],
                    "detail": f"Membership expired {match['expiry_date']}",
                    "member": match,
                }
        except Exception:
            pass

    if (match.get("status") or "active").lower() not in ("active",):
        return {"kind": "error", "name": match["full_name"],
                "detail": f"Account {match.get('status','Inactive')}",
                "member": match}

    db.mark_attendance(match["id"], match["gym_id"], date.today(), "Present", current_user)
    st.session_state.face_enc_cache = None

    return {
        "kind": "success",
        "name": f"WELCOME {match['full_name']}",
        "detail": f"✅ Attendance mark · {match['score']*100:.0f}% match",
        "member": match,
    }

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

@st.fragment
def _face_camera_fragment(face_gym_id, current_user):
    st.components.v1.html(_AUTOCLICK_JS, height=0)
    
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
            st.session_state.face_cam_gen += 1
            st.image(pil, use_container_width=True)
            
            if result["kind"] == "success":
                st.success(f"✅ {result['name']}")
                st.components.v1.html(_BEEP_JS, height=0)
            elif result["kind"] == "unknown":
                st.warning(f"❓ {result['name']} - {result['detail']}")
                st.components.v1.html(_BUZZ_JS, height=0)
            elif result["kind"] == "expired":
                st.error(f"⚠️ {result['name']} - {result['detail']}")
                st.components.v1.html(_BUZZ_JS, height=0)
            else:
                st.info(f"ℹ️ {result['name']} - {result['detail']}")
            
            st.rerun(scope="fragment")
    else:
        st.markdown(
            '<div style="background:#0F172A;border:2px dashed #1E293B;'
            'border-radius:12px;padding:2rem;text-align:center;color:#475569;">'
            "🎥 Camera ready — Click 'Take Photo' to start"
            "</div>",
            unsafe_allow_html=True,
        )

def render_face_recognition_tab(gym_id, current_user):
    if not st.session_state.get('face_enabled', False):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("⚠️ Face Recognition is disabled for faster loading")
            if st.button("📸 Enable Face Recognition", use_container_width=True, type="primary"):
                st.session_state.face_enabled = True
                st.rerun()
        return
    
    _face_ss_init()
    _run_cleanup()
    
    if gym_id:
        st.caption(f"📍 Gym: {db.get_gym(gym_id).name if gym_id else ''}")
    
    enc_count = len(db.get_face_encodings(gym_id))
    if enc_count == 0:
        st.warning("⚠️ Koi face encoding nahi hai. Members page par photos upload karein.")
    else:
        st.caption(f"✅ {enc_count} member faces ready · Threshold: {FACE_THRESHOLD}")
    
    if st.button("🔴 Disable Face Recognition", use_container_width=True):
        st.session_state.face_enabled = False
        st.rerun()
    
    _face_camera_fragment(gym_id, current_user)

# ════════════════════════════════════════════════════════════════════════════
# 🚀 TOP DASHBOARD - DATE/TIME DISPLAY
# ════════════════════════════════════════════════════════════════════════════

def render_top_dashboard(sel_gid):
    """Display current date and time at top of dashboard"""
    
    now = datetime.now()
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                border:1px solid #7C3AED;border-radius:16px;
                padding:1rem 1.5rem;margin-bottom:1rem;
                box-shadow:0 0 40px rgba(124,58,237,0.1);">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:15px;">
                <span style="font-size:2rem;">🕐</span>
                <div>
                    <div style="font-size:1.4rem;font-weight:800;color:#FFC947;">
                        {now.strftime('%I:%M:%S %p')}
                    </div>
                    <div style="color:#94A3B8;font-size:0.8rem;">
                        {now.strftime('%A, %d %B %Y')}
                    </div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#34D399;font-size:0.8rem;font-weight:600;">
                    🟢 System Live
                </div>
                <div style="color:#64748B;font-size:0.7rem;">
                    Last Updated: {now.strftime('%H:%M:%S')}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# 🤖 SMART AI ASSISTANT - DEFINED
# ════════════════════════════════════════════════════════════════════════════

def render_smart_ai_assistant(sel_gid, gym_name):
    """Smart AI Assistant - Complete"""
    
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                border:1px solid #7C3AED;border-radius:16px;
                padding:1rem 1.5rem;margin-bottom:1rem;
                box-shadow:0 0 40px rgba(124,58,237,0.1);">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:2rem;">🤖</span>
            <div>
                <span style="font-size:1.1rem;font-weight:700;color:#FFFFFF;">Smart AI Assistant</span>
                <span style="color:#94A3B8;font-size:0.8rem;margin-left:8px;">🔴 Live · Analyzing patterns</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("🤖 AI analyzing data..."):
        all_members = db.get_members(gym_id=sel_gid)
        active_members = [m for m in all_members if m.status == "Active"]
        
        today = date.today()
        today_attendance = db.get_attendance(gym_id=sel_gid, check_date=today)
        present_today = [a for a in today_attendance if a.status == "Present"]
        absent_today = [a for a in today_attendance if a.status == "Absent"]
        late_today = [a for a in today_attendance if a.status == "Late"]
        
        trend_data = db.get_attendance_trend(gym_id=sel_gid, days=30)
        absent_members = db.get_absent_members(days=3, gym_id=sel_gid)
        expiring_members = db.get_expiring_members(days=7, gym_id=sel_gid)
        hourly_data = db.get_attendance_by_hour(gym_id=sel_gid)
        
        streak_data = []
        for m in active_members[:30]:
            s = db.get_member_streak(m.id)
            if s >= 3:
                streak_data.append({"member": m, "streak": s})
        streak_data.sort(key=lambda x: x["streak"], reverse=True)
        
        total_active = len(active_members)
        total_present = len(present_today)
        attendance_rate = round((total_present / total_active * 100) if total_active > 0 else 0, 1)
        
        if trend_data:
            avg_attendance = round(sum(t["present"] for t in trend_data) / len(trend_data), 1)
        else:
            avg_attendance = 0
        
        peak_hour = max(hourly_data, key=hourly_data.get) if hourly_data and any(hourly_data.values()) else None

    st.markdown("### 📊 Live Stats")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("👥 Total Active", total_active)
    with col2:
        st.metric("✅ Today Present", total_present, delta=f"{attendance_rate}%")
    with col3:
        st.metric("⏳ Absent", len(absent_today))
    with col4:
        st.metric("🕐 Late", len(late_today))
    with col5:
        st.metric("🔥 Top Streak", streak_data[0]["streak"] if streak_data else 0)
    
    st.divider()
    
    st.markdown("### 💡 Smart Insights")
    
    insights = []
    
    if attendance_rate >= 80:
        insights.append({"icon": "🌟", "title": "Excellent Attendance!", "detail": f"{attendance_rate}% attendance rate today.", "color": "#10B981", "action": "Keep up the great work!"})
    elif attendance_rate >= 60:
        insights.append({"icon": "📈", "title": "Good Attendance", "detail": f"{attendance_rate}% attendance rate today.", "color": "#FBBF24", "action": "Consider sending reminders."})
    else:
        insights.append({"icon": "⚠️", "title": "Low Attendance Alert", "detail": f"Only {attendance_rate}% of members attended today.", "color": "#EF4444", "action": "🏃 Send WhatsApp reminders!"})
    
    if trend_data and len(trend_data) >= 7:
        last_week_avg = sum(t["present"] for t in trend_data[-7:]) / 7
        prev_week_avg = sum(t["present"] for t in trend_data[-14:-7]) / 7 if len(trend_data) >= 14 else last_week_avg
        trend_change = round(((last_week_avg - prev_week_avg) / prev_week_avg * 100) if prev_week_avg > 0 else 0, 1)
        if trend_change > 10:
            insights.append({"icon": "📈", "title": f"Attendance Growing! +{trend_change}%", "color": "#10B981", "action": "✅ Great momentum!"})
        elif trend_change < -10:
            insights.append({"icon": "📉", "title": f"Attendance Dropping! {trend_change}%", "color": "#EF4444", "action": "⚠️ Investigate decline."})
    
    if peak_hour is not None:
        insights.append({"icon": "⏰", "title": f"Peak Hour: {peak_hour:02d}:00", "detail": f"{hourly_data.get(peak_hour, 0)} check-ins", "color": "#8B5CF6", "action": f"💡 Add extra staff at {peak_hour:02d}:00."})
    
    if len(absent_members) > 5:
        insights.append({"icon": "🚨", "title": f"{len(absent_members)} Members Absent 3+ Days", "color": "#EF4444", "action": "📱 Send WhatsApp messages."})
    
    if len(expiring_members) > 0:
        insights.append({"icon": "⏰", "title": f"{len(expiring_members)} Members Expiring Soon", "color": "#F59E0B", "action": "💰 Send renewal reminders."})
    
    if streak_data:
        insights.append({"icon": "🔥", "title": f"Top Streak: {streak_data[0]['streak']} days", "color": "#FF6B6B", "action": "🎖️ Reward top attenders!"})
    
    for insight in insights[:6]:
        st.markdown(f"""
        <div style="background:{insight['color']}08;border-left:4px solid {insight['color']};
                    border-radius:10px;padding:0.6rem 1rem;margin-bottom:0.4rem;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.3rem;">{insight['icon']}</span>
                <div style="flex:1;">
                    <div style="color:#F8FAFC;font-weight:600;font-size:0.9rem;">{insight['title']}</div>
                    <div style="color:{insight['color']};font-size:0.75rem;font-weight:500;">💡 {insight['action']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption(f"🤖 AI analyzed {len(all_members)} members · Last updated: {datetime.now().strftime('%H:%M')}")

# ════════════════════════════════════════════════════════════════════════════
# 🚀 STAFF ATTENDANCE SYSTEM
# ════════════════════════════════════════════════════════════════════════════

def render_staff_attendance_system(sel_gid, current_user):
    """Complete Staff Attendance System with Time Check & AI Warnings"""
    
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                border:2px solid #7C3AED;border-radius:16px;
                padding:1rem 1.5rem;margin-bottom:1rem;
                box-shadow:0 0 40px rgba(124,58,237,0.1);">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.8rem;">👤</span>
                <div>
                    <div style="font-size:1.2rem;font-weight:700;color:#FFFFFF;">
                        Staff Attendance System
                    </div>
                    <div style="color:#94A3B8;font-size:0.75rem;">
                        ⏰ Time-based check-in/out with AI warnings
                    </div>
                </div>
            </div>
            <div style="color:#94A3B8;font-size:0.7rem;">
                {datetime.now().strftime('%I:%M:%S %p')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Get All Staff ──────────────────────────────────────────────────────
    all_users = db.get_all_users()
    gym_staff = [u for u in all_users if u.gym_id == sel_gid and u.role != 'admin']
    
    if not gym_staff:
        st.info("📭 No staff members found. Add staff from Gym Setup.")
        return
    
    today = date.today()
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    # ── Staff Selector ──────────────────────────────────────────────────
    st.markdown("### 📌 Select Staff Member")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        staff_opts = {f"{u.full_name} (ID: {u.id})": u.username for u in gym_staff}
        selected_staff_label = st.selectbox(
            "👤 Select Staff Member",
            list(staff_opts.keys()),
            key="staff_att_select_main"
        )
        staff_username = staff_opts[selected_staff_label]
        selected_staff = next((u for u in gym_staff if u.username == staff_username), None)
    
    with col2:
        # Get staff timing
        staff_timing = db.get_staff_timing(staff_username)
        if staff_timing:
            st.info(f"⏰ Timing: {staff_timing['check_in_time']} - {staff_timing['check_out_time']}")
        else:
            st.warning("⚠️ No timing set. Admin should set timing.")
    
    if not selected_staff:
        return
    
    # ── Get Today's Status ──────────────────────────────────────────────
    check_in_record = None
    try:
        records = db.get_staff_attendance(staff_username=staff_username, date_from=today, date_to=today)
        for r in records:
            if r.logout_time is None:
                check_in_record = r
                break
    except:
        pass
    
    # ── Staff Timing ──────────────────────────────────────────────────────
    if not staff_timing:
        st.warning("⚠️ Staff timing not set. Please ask admin to set your timing.")
        if st.button("⏰ Set My Timing Now", use_container_width=True):
            st.session_state['page'] = "Gym Setup"
            st.rerun()
        return
    
    check_in_time = staff_timing['check_in_time']
    check_out_time = staff_timing['check_out_time']
    grace_minutes = staff_timing.get('grace_minutes', 15)
    
    # ── AI Status Check ──────────────────────────────────────────────────
    status_message = ""
    status_color = "#10B981"
    status_icon = "✅"
    
    if not check_in_record:
        if current_time < check_in_time:
            early_minutes = (datetime.strptime(check_in_time, "%H:%M") - datetime.strptime(current_time, "%H:%M")).seconds // 60
            if early_minutes > 30:
                status_message = f"⏰ Too early! Shift starts at {check_in_time}. Please wait."
                status_color = "#EF4444"
                status_icon = "⚠️"
            elif early_minutes > 0:
                status_message = f"🟡 You're {early_minutes} minutes early. Shift starts at {check_in_time}."
                status_color = "#F59E0B"
                status_icon = "🟡"
            else:
                status_message = f"✅ You're on time! Shift starts at {check_in_time}."
                status_color = "#10B981"
                status_icon = "✅"
        elif current_time > check_in_time:
            late_minutes = (datetime.strptime(current_time, "%H:%M") - datetime.strptime(check_in_time, "%H:%M")).seconds // 60
            if late_minutes <= grace_minutes:
                status_message = f"🟡 You're {late_minutes} minutes late (Grace period: {grace_minutes} min)."
                status_color = "#F59E0B"
                status_icon = "🟡"
            else:
                status_message = f"⚠️ You're {late_minutes} minutes late! Please check-in now."
                status_color = "#EF4444"
                status_icon = "⚠️"
        else:
            status_message = f"✅ Ready to check-in! Shift starts at {check_in_time}."
            status_color = "#10B981"
            status_icon = "✅"
    else:
        checkin_time_display = check_in_record.login_time
        if current_time > check_out_time:
            status_message = f"⏰ Shift ended at {check_out_time}. Please check-out."
            status_color = "#F59E0B"
            status_icon = "🕐"
        else:
            remaining = (datetime.strptime(check_out_time, "%H:%M") - datetime.strptime(current_time, "%H:%M")).seconds // 60
            status_message = f"✅ Online! {remaining} minutes remaining in shift."
            status_color = "#10B981"
            status_icon = "✅"
    
    # ── AI Warning Banner ──────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{status_color}08;border-left:5px solid {status_color};
                border-radius:10px;padding:0.8rem 1.2rem;margin:0.5rem 0 1rem 0;">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:1.5rem;">{status_icon}</span>
            <div>
                <div style="color:#F8FAFC;font-size:0.95rem;font-weight:600;">
                    AI Status: {status_message}
                </div>
                <div style="color:#94A3B8;font-size:0.75rem;">
                    Staff: {selected_staff.full_name} · Shift: {check_in_time} - {check_out_time} · Grace: {grace_minutes}min
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Staff Info Cards ──────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👤 Staff", selected_staff.full_name)
    with col2:
        status_text = "🟢 Online" if check_in_record else "⚪ Offline"
        st.metric("📊 Status", status_text)
    with col3:
        checkin_time_display = check_in_record.login_time.strftime("%I:%M %p") if check_in_record else "—"
        st.metric("⏰ Check-in", checkin_time_display)
    with col4:
        st.metric("🎯 Shift", f"{check_in_time} - {check_out_time}")
    
    st.divider()
    
    # ── Action Buttons ──────────────────────────────────────────────────────
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if not check_in_record:
            can_checkin = True
            warning_msg = ""
            
            if current_time < check_in_time:
                early_minutes = (datetime.strptime(check_in_time, "%H:%M") - datetime.strptime(current_time, "%H:%M")).seconds // 60
                if early_minutes > 30:
                    can_checkin = False
                    warning_msg = f"⚠️ Too early! Shift starts at {check_in_time}. Please wait {early_minutes} minutes."
                else:
                    warning_msg = f"🟡 You're {early_minutes} minutes early. Check-in anyway?"
            
            if can_checkin:
                if st.button(f"✅ Check-in {selected_staff.full_name}", use_container_width=True, type="primary"):
                    ok, msg = db.log_staff_login(staff_username, ip_address="Manual Check-in")
                    if ok:
                        checkin_status = "on-time"
                        if current_time > check_in_time:
                            late_minutes = (datetime.strptime(current_time, "%H:%M") - datetime.strptime(check_in_time, "%H:%M")).seconds // 60
                            if late_minutes <= grace_minutes:
                                checkin_status = "grace"
                            else:
                                checkin_status = "late"
                        elif current_time < check_in_time:
                            checkin_status = "early"
                        
                        st.success(f"✅ {selected_staff.full_name} checked IN at {datetime.now().strftime('%I:%M %p')}")
                        st.balloons()
                        
                        if checkin_status == "early":
                            st.warning(f"⚠️ You checked in EARLY! (Shift starts at {check_in_time})")
                        elif checkin_status == "grace":
                            st.warning(f"🟡 You checked in LATE but within grace period. ({late_minutes} min late)")
                        elif checkin_status == "late":
                            st.error(f"❌ You checked in LATE! ({late_minutes} minutes late)")
                        else:
                            st.success("✅ Perfect timing! On-time check-in.")
                        
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            else:
                st.button(f"⏳ Wait until {check_in_time}", use_container_width=True, disabled=True)
                st.warning(warning_msg)
        else:
            st.button(f"✅ {selected_staff.full_name} is Online", use_container_width=True, disabled=True)
    
    with col_btn2:
        if check_in_record:
            can_checkout = True
            checkout_warning = ""
            
            if current_time < check_out_time:
                remaining = (datetime.strptime(check_out_time, "%H:%M") - datetime.strptime(current_time, "%H:%M")).seconds // 60
                if remaining > 30:
                    can_checkout = False
                    checkout_warning = f"⚠️ Shift ends at {check_out_time}. {remaining} minutes remaining."
                else:
                    checkout_warning = f"🟡 {remaining} minutes remaining. Early check-out?"
            
            if can_checkout:
                if st.button(f"🔴 Check-out {selected_staff.full_name}", use_container_width=True, type="primary"):
                    ok, msg = db.log_staff_logout(staff_username)
                    if ok:
                        duration = datetime.now() - check_in_record.login_time
                        hours = duration.seconds // 3600
                        minutes = (duration.seconds % 3600) // 60
                        
                        st.success(f"✅ {selected_staff.full_name} checked OUT at {datetime.now().strftime('%I:%M %p')}")
                        st.info(f"⏱️ Total Duration: {hours}h {minutes}m")
                        
                        if current_time < check_out_time:
                            remaining = (datetime.strptime(check_out_time, "%H:%M") - datetime.strptime(current_time, "%H:%M")).seconds // 60
                            if remaining > 30:
                                st.warning(f"⚠️ EARLY CHECK-OUT! ({remaining} minutes early)")
                            else:
                                st.warning(f"🟡 Early check-out by {remaining} minutes")
                        else:
                            st.success("✅ Completed full shift!")
                        
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            else:
                st.button(f"⏳ Shift ends at {check_out_time}", use_container_width=True, disabled=True)
                if checkout_warning:
                    st.warning(checkout_warning)
        else:
            st.button(f"🔴 {selected_staff.full_name} is Offline", use_container_width=True, disabled=True)
    
    with col_btn3:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # ── Staff History ──────────────────────────────────────────────────────
    st.divider()
    st.markdown(f"### 📋 {selected_staff.full_name}'s Attendance History")
    
    month_start = today - timedelta(days=30)
    history = db.get_staff_attendance(
        staff_username=staff_username,
        date_from=month_start,
        date_to=today
    )
    
    if history:
        data = []
        total_hours = 0
        total_days = len(history)
        completed = 0
        late_count = 0
        early_count = 0
        
        for r in history:
            login = r.login_time.strftime("%I:%M %p") if r.login_time else "—"
            logout = r.logout_time.strftime("%I:%M %p") if r.logout_time else "—"
            
            duration_minutes = r.session_duration or 0
            duration_hours = duration_minutes // 60
            duration_mins = duration_minutes % 60
            duration_str = f"{duration_hours}h {duration_mins}m"
            total_hours += duration_hours
            
            status = "🟢 Online" if r.logout_time is None else "✅ Completed"
            if r.logout_time is not None:
                completed += 1
            
            checkin_status = "✅ On-Time"
            if r.login_time:
                login_time_str = r.login_time.strftime("%H:%M")
                if login_time_str > check_in_time:
                    diff = (datetime.strptime(login_time_str, "%H:%M") - datetime.strptime(check_in_time, "%H:%M")).seconds // 60
                    if diff > grace_minutes:
                        checkin_status = "🔴 Late"
                        late_count += 1
                    else:
                        checkin_status = "🟡 Grace"
                elif login_time_str < check_in_time:
                    checkin_status = "🟡 Early"
                    early_count += 1
            
            data.append({
                "Date": r.login_time.strftime("%d %b") if r.login_time else "—",
                "Check-in": login,
                "Check-out": logout,
                "Duration": duration_str,
                "Status": status,
                "Check-in Status": checkin_status
            })
        
        data = sorted(data, key=lambda x: x["Date"], reverse=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📅 Total Days", total_days)
        with col2:
            st.metric("⏱️ Total Hours", f"{total_hours}h")
        with col3:
            attendance_rate = round((completed / total_days * 100) if total_days > 0 else 0, 1)
            st.metric("📊 Rate", f"{attendance_rate}%")
        with col4:
            st.metric("🔴 Late", late_count, delta="⚠️ Needs improvement")
        with col5:
            st.metric("🟡 Early", early_count)
        
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        
        if late_count > total_days * 0.3:
            st.error(f"⚠️ AI Alert: {late_count} late days ({round(late_count/total_days*100)}%) - Staff needs to improve punctuality!")
        elif late_count > 0:
            st.warning(f"🟡 AI Note: {late_count} late days - Consider reminding staff about timing.")
        else:
            st.success("✅ Excellent punctuality! No late days.")
    else:
        st.info("📭 No attendance records for this staff member")

# ════════════════════════════════════════════════════════════════════════════
# STATS BAR
# ════════════════════════════════════════════════════════════════════════════

def _today_kpi_bar(sel_gid):
    members = _cached_gym_members(sel_gid, "Active")
    total = len(members)
    att_today = _cached_today_attendance(sel_gid)
    present = sum(1 for a in att_today if a.status == "Present")
    absent = sum(1 for a in att_today if a.status == "Absent")
    late = sum(1 for a in att_today if a.status == "Late")
    pct = round(present / total * 100) if total else 0
    alert_cnt = len(_cached_absent_members(sel_gid, days=3))
    unmarked = total - len(att_today)

    st.markdown(f"""
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:1rem;">
      <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#064E3B,#065F46);
           border:1px solid #10B981;border-radius:12px;padding:0.7rem 0.8rem;text-align:center;">
        <div style="font-size:1.8rem;font-weight:900;color:#10B981;">{present}</div>
        <div style="font-size:0.7rem;color:#6EE7B7;">✅ Present</div>
        <div style="font-size:0.65rem;color:#34D399;">{pct}% of {total}</div>
      </div>
      <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#1E293B,#0F172A);
           border:1px solid #475569;border-radius:12px;padding:0.7rem 0.8rem;text-align:center;">
        <div style="font-size:1.8rem;font-weight:900;color:#94A3B8;">{unmarked}</div>
        <div style="font-size:0.7rem;color:#94A3B8;">⏳ Pending</div>
        <div style="font-size:0.65rem;color:#64748B;">{len(att_today)}/{total}</div>
      </div>
      <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#7F1D1D,#991B1B);
           border:1px solid #EF4444;border-radius:12px;padding:0.7rem 0.8rem;text-align:center;">
        <div style="font-size:1.8rem;font-weight:900;color:#FCA5A5;">{alert_cnt}</div>
        <div style="font-size:0.7rem;color:#FCA5A5;">🚨 Absent 3+</div>
      </div>
      <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#1E1B4B,#312E81);
           border:1px solid #818CF8;border-radius:12px;padding:0.7rem 0.8rem;text-align:center;">
        <div style="font-size:1.8rem;font-weight:900;color:#818CF8;">{late}</div>
        <div style="font-size:0.7rem;color:#A5B4FC;">🕐 Late</div>
      </div>
      <div style="flex:1;min-width:110px;background:linear-gradient(135deg,#0C4A6E,#075985);
           border:1px solid #38BDF8;border-radius:12px;padding:0.7rem 0.8rem;text-align:center;">
        <div style="font-size:1.2rem;font-weight:900;color:#38BDF8;">{date.today().strftime('%d %b')}</div>
        <div style="font-size:0.72rem;color:#7DD3FC;">{date.today().strftime('%A')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# QR GENERATOR
# ════════════════════════════════════════════════════════════════════════════

def render_qr_generator(sel_gid):
    st.subheader("📱 Generate QR Codes")
    members = _cached_gym_members(sel_gid, "Active")
    if not members:
        st.info("No active members")
        return
    
    selected = st.multiselect(
        "Select Members",
        options=[(m.id, f"{m.full_name} ({m.serial_number})") for m in members[:50]],
        format_func=lambda x: x[1]
    )
    
    if selected and st.button("🖨️ Generate", use_container_width=True, type="primary"):
        cols = st.columns(4)
        for idx, (mid, _) in enumerate(selected[:8]):
            m = db.get_member(mid)
            if m:
                qr = qrcode.QRCode(version=1, box_size=6, border=3)
                qr.add_data(json.dumps({"member_id": m.id, "serial": m.serial_number, "name": m.full_name}))
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                buffered.seek(0)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                with cols[idx % 4]:
                    st.image(f"data:image/png;base64,{img_str}", width=120)
                    st.caption(m.full_name[:15])
                    st.download_button("⬇️ QR", data=buffered.getvalue(), file_name=f"{m.serial_number}_qr.png", mime="image/png", key=f"qr_{m.id}")

# ════════════════════════════════════════════════════════════════════════════
# PRINT SHEET
# ════════════════════════════════════════════════════════════════════════════

def render_print_attendance(sel_gid):
    st.subheader("🖨️ Print Sheet")
    att_date = st.date_input("Date", value=date.today())
    attendance = _cached_today_attendance(sel_gid) if att_date == date.today() else db.get_attendance(gym_id=sel_gid, check_date=att_date)
    members = _cached_gym_members(sel_gid, "Active")
    
    data = []
    for m in members[:30]:
        att = next((a for a in attendance if a.member_id == m.id), None)
        data.append({
            "Serial": m.serial_number,
            "Name": m.full_name,
            "Status": att.status if att else "—",
            "Time": att.created_at.strftime("%H:%M") if att and att.created_at else "—",
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🖨️ Print", use_container_width=True, type="primary"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# STAFF ATTENDANCE SUMMARY
# ════════════════════════════════════════════════════════════════════════════

def render_staff_attendance(sel_gid):
    st.subheader("👥 Staff Attendance Summary")
    
    all_users = db.get_all_users()
    gym_staff = [u for u in all_users if u.gym_id == sel_gid and u.role != 'admin']
    if not gym_staff:
        st.info("No staff found")
        return
    
    try:
        staff_summary = db.get_staff_attendance_summary(gym_id=sel_gid)
    except:
        staff_summary = []
    
    if staff_summary:
        data = []
        for s in staff_summary:
            data.append({
                "Name": s['full_name'],
                "Role": s['role'],
                "Status": s['status'],
                "Hours": f"{s['total_hours']}h"
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No data available")

# ════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN RENDER
# ════════════════════════════════════════════════════════════════════════════

def render(gym_id, role, current_user):
    init_session_state()

    styles.page_header("📅", "Attendance Management",
                       "Smart tracking with QR scan, face recognition, analytics & AI alerts")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    gym_opts = {g.name: g.id for g in gyms}

    if gym_id:
        sel_gid = gym_id
        gname = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
    else:
        chosen = st.selectbox("📍 Select Gym", list(gym_opts.keys()), key="att_main_gym_top")
        sel_gid = gym_opts[chosen]
        gname = chosen

    # ✅ TOP DASHBOARD - Date/Time Display
    render_top_dashboard(sel_gid)

    # Clear Cache Button
    col_clear1, col_clear2 = st.columns([6, 1])
    with col_clear2:
        if st.button("🔄 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.session_state.attendance_photo_cache = {}
            st.rerun()

    # Quick Stats Bar
    _today_kpi_bar(sel_gid)

    # ⚡ TABS
    tabs = [
        "🎯 QR Scan",
        "✅ Manual Mark",
        "📸 Face Check-in",
        "📊 Analytics",
        "📋 Records",
        "📱 QR Generate",
        "🖨️ Print Sheet",
        "👥 Staff Attendance"
    ]
    
    tab_objs = st.tabs(tabs)

    # ── TAB 1: QR Scan ────────────────────────────────────────────────────
    with tab_objs[0]:
        st.components.v1.html(_AUDIO_PRIMER_JS, height=0)
        st.caption(f"📍 Scanning at: **{gname}** · {date.today().isoformat()}")

        last = st.session_state.get("qr_last_result")
        if last:
            if last["kind"] == "success":
                _big_banner("#064E3B", "#10B981", f'{last["headline"]} · {last["sub"]}', icon="✅")
                _play("beep")
                m = last.get("member")
                if m:
                    show_member_photo(m.photo_path, width=160)
                    st.caption(f"Serial **{m.serial_number}** · {m.membership_type} · expires {m.expiry_date or '—'}")
            elif last["kind"] == "expired":
                _big_banner("#7F1D1D", "#EF4444", "⚠️ FEES EXPIRED", last["sub"], icon="🚫")
                _play("buzz")
                m = last.get("member")
                if m:
                    show_member_photo(m.photo_path, width=160)
            else:
                _big_banner("#7F1D1D", "#EF4444", last["headline"], last["sub"], icon="❌")
                _play("buzz")

        with st.form("qr_scan_form", clear_on_submit=True):
            st.text_input(
                "Scan member QR code",
                key="qr_scan_input",
                placeholder="Scan now — or type a serial and press Enter",
                autocomplete="off",
            )
            submitted = st.form_submit_button("✓ Check In", type="primary", use_container_width=True)
        if submitted:
            raw = st.session_state.get("qr_scan_input", "")
            st.session_state["qr_last_result"] = _process_scan(raw, sel_gid, current_user)
            st.rerun()

        _autofocus_scan_input()
        st.divider()
        
        with st.expander("🤖 AI Insights (Click to load)", expanded=False):
            render_smart_ai_assistant(sel_gid, gname)

        recent = _cached_recent_scans(sel_gid, 100)
        
        st.markdown("##### 🟢 Inside Gym Right Now")
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

        st.metric("Live Counter", f"{len(inside_now)} Members")

        if inside_now:
            df_live = pd.DataFrame([
                {"Time": r["time"], "Serial": r["serial"], "Member": r["name"]}
                for r in inside_now
            ])
            st.dataframe(df_live, use_container_width=True, hide_index=True)

        st.markdown("##### 📋 Today's Attendance")
        if recent:
            df_all = pd.DataFrame([
                {"Time": r["time"], "Serial": r["serial"], "Name": r["name"], "Marked By": r["marked_by"]}
                for r in recent
            ])
            st.dataframe(df_all, use_container_width=True, hide_index=True, height=min(200, 50 + 35 * len(recent)))
        else:
            st.caption("No check-ins yet today.")

    # ── TAB 2: Manual Mark ─────────────────────────────────────────────────
    with tab_objs[1]:
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.text_input("Gym", value=gname, disabled=True, key="att_gym_display")
        with mc2:
            att_date = st.date_input("Date", value=date.today(), key="att_date")
        with mc3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.pop(f"marked_today_{sel_gid}_{att_date}", None)
                st.rerun()

        all_active = _cached_gym_members(sel_gid, "Active")
        existing = {a.member_id: a.status for a in _cached_today_attendance(sel_gid)}

        session_key = f"marked_today_{sel_gid}_{att_date}"
        if session_key not in st.session_state:
            st.session_state[session_key] = set(existing.keys())

        pending = [m for m in all_active if m.id not in st.session_state[session_key]]
        marked = [m for m in all_active if m.id in st.session_state[session_key]]

        total = len(all_active)
        done = len(marked)
        progress = (done / total * 100) if total > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Total", total)
        with col2:
            st.metric("✅ Done", done)
        with col3:
            st.metric("⏳ Pending", len(pending))
        with col4:
            st.metric("📊 Progress", f"{progress:.0f}%")

        if total > 0:
            st.progress(progress / 100)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✅ Mark ALL Present", use_container_width=True, type="primary"):
                for m in pending:
                    db.mark_attendance(m.id, sel_gid, att_date, "Present", current_user)
                    st.session_state[session_key].add(m.id)
                st.rerun()
        with col_b2:
            if st.button("❌ Mark ALL Absent", use_container_width=True):
                for m in pending:
                    db.mark_attendance(m.id, sel_gid, att_date, "Absent", current_user)
                    st.session_state[session_key].add(m.id)
                st.rerun()

        st.divider()

        search_q = st.text_input("🔍 Search", placeholder="Name or Serial...", key="manual_search")
        if search_q:
            q = search_q.lower()
            pending = [m for m in pending if q in m.full_name.lower() or q in (m.serial_number or "").lower()]

        st.markdown(f"### 📋 Pending ({len(pending)})")

        for m in pending[:30]:
            with st.container():
                col_pic, col_info, col_btn = st.columns([1, 3, 1.5])

                with col_pic:
                    show_member_photo(m.photo_path, width=70)

                with col_info:
                    st.markdown(f"**{m.full_name}**")
                    st.caption(f"🆔 {m.serial_number} · {m.membership_type or '—'}")

                with col_btn:
                    if st.button("✅ Present", key=f"p_{m.id}", use_container_width=True, type="primary"):
                        db.mark_attendance(m.id, sel_gid, att_date, "Present", current_user)
                        st.session_state[session_key].add(m.id)
                        st.rerun()
                
                st.divider()

        if len(pending) > 30:
            st.info(f"📌 Showing 30 of {len(pending)} pending members")

        if marked:
            with st.expander(f"✅ Already Marked ({len(marked)})"):
                df_marked = pd.DataFrame([{
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Status": existing.get(m.id, "—")
                } for m in marked])
                st.dataframe(df_marked, use_container_width=True, hide_index=True)

    # ── TAB 3: Face Check-in ─────────────────────────────────────────────
    with tab_objs[2]:
        render_face_recognition_tab(sel_gid, current_user)

    # ── TAB 4: Analytics ──────────────────────────────────────────────────
    with tab_objs[3]:
        st.markdown("#### 📈 30-Day Trend")
        trend = _cached_attendance_trend(sel_gid, days=30)
        if trend and _PLOTLY:
            df_t = pd.DataFrame(trend)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Present", x=df_t["date"], y=df_t["present"], marker_color="#10B981"))
            fig.add_trace(go.Bar(name="Late", x=df_t["date"], y=df_t["late"], marker_color="#F59E0B"))
            fig.add_trace(go.Bar(name="Absent", x=df_t["date"], y=df_t["absent"], marker_color="#EF4444"))
            fig.update_layout(
                barmode="stack",
                plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
                font=dict(color="#F8FAFC"),
                legend=dict(orientation="h", y=1.12, x=0),
                margin=dict(l=0, r=0, t=30, b=0),
                height=260,
            )
            st.plotly_chart(fig, use_container_width=True)
            
            avg = round(sum(t["present"] for t in trend) / len(trend), 1)
            max_day = max(trend, key=lambda t: t["present"])
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 Avg Present", avg)
            c2.metric("🔝 Best", f"{max_day['date']} ({max_day['present']})")
            c3.metric("📉 Days", len(trend))
        else:
            st.info("No data yet")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### 🕐 Peak Hours")
            hourly = _cached_attendance_by_hour(sel_gid)
            if hourly and _PLOTLY and any(hourly.values()):
                hours = list(range(24))
                counts = [hourly.get(h, 0) for h in hours]
                colors = ["#F59E0B" if c == max(counts) else "#3B82F6" for c in counts]
                fig2 = go.Figure(go.Bar(x=[f"{h:02d}:00" for h in hours], y=counts, marker_color=colors))
                fig2.update_layout(
                    plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
                    height=240, margin=dict(l=0, r=0, t=10, b=0),
                )
                st.plotly_chart(fig2, use_container_width=True)
                peak = max(hourly, key=hourly.get)
                st.caption(f"🏆 Peak: **{peak:02d}:00** ({hourly[peak]} check-ins)")
            else:
                st.info("No data")

        with col_r:
            st.markdown("#### 🏆 Top Attenders")
            leaders = _cached_leaderboard(sel_gid, limit=8)
            if leaders:
                for i, ld in enumerate(leaders):
                    m = ld["member"]
                    medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**{i+1}.**"
                    s_badge = f" 🔥{ld.get('streak', 0)}d" if ld.get('streak', 0) >= 3 else ""
                    st.markdown(
                        f"""<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #1E293B;">
                          <span style="font-size:1rem;min-width:22px;">{medal}</span>
                          <span style="color:#F8FAFC;font-weight:600;flex:1;">{m.full_name}</span>
                          <span style="color:#10B981;">{ld['count']}d{s_badge}</span>
                        </div>""",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No data")

        absent_members = _cached_absent_members(sel_gid, 3)
        if absent_members:
            st.warning(f"⚠️ {len(absent_members)} members absent 3+ days")

    # ── TAB 5: Records ────────────────────────────────────────────────────
    with tab_objs[4]:
        st.markdown("### 📋 Records")
        from_date = date.today() - timedelta(days=6)
        to_date = date.today()
        records = db.get_attendance_range(gym_id=sel_gid, from_date=from_date, to_date=to_date)
        
        if records:
            rows = []
            for r in records[:50]:
                m = db.get_member(r.member_id)
                rows.append({
                    "Date": r.check_date,
                    "Serial": m.serial_number if m else "—",
                    "Name": m.full_name if m else "—",
                    "Status": r.status,
                    "Time": r.created_at.strftime("%H:%M") if r.created_at else "—",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            
            csv_buf = io.StringIO()
            pd.DataFrame(rows).to_csv(csv_buf, index=False)
            st.download_button("⬇️ Export CSV", data=csv_buf.getvalue(), file_name=f"attendance_{from_date}_{to_date}.csv", mime="text/csv")
        else:
            st.info("No records found")

    # ── TAB 6: QR Generate ────────────────────────────────────────────────
    with tab_objs[5]:
        render_qr_generator(sel_gid)

    # ── TAB 7: Print Sheet ────────────────────────────────────────────────
    with tab_objs[6]:
        render_print_attendance(sel_gid)

    # ── TAB 8: Staff Attendance ──────────────────────────────────────────
    with tab_objs[7]:
        render_staff_attendance_system(sel_gid, current_user)