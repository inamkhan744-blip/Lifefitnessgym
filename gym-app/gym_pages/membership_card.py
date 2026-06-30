import streamlit as st
import base64
import os
import json
from datetime import date, datetime
import database as db
import styles
import object_store
from PIL import Image, ImageOps
import io

UPLOAD_DIR = "gym-app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_session_state():
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

init_session_state()

CACHE_FILE = "gym_app_cache_last_card.json"
GALLERY_CACHE_FILE = "gym_app_gallery_cache.json"

STATUS_COLORS = {
    "Active":    ("#064E3B", "#34D399"),
    "Inactive":  ("#450A0A", "#F87171"),
    "Suspended": ("#451A03", "#FBBF24"),
    "Frozen":    ("#0C1A3A", "#60A5FA"),
}

# ============================================
# 🔥 FIXED: Image Orientation Fix - Strong
# ============================================

def fix_image_orientation(img):
    """Fix image orientation using EXIF data - STRONG FIX"""
    try:
        # Method 1: EXIF orientation
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
    
    # Method 2: ImageOps exif_transpose - automatically fixes orientation
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass
    
    return img

# ============================================
# 🔥 FIXED: Compress Image with Orientation Fix
# ============================================

def compress_image(image_path, max_size_kb=50, quality=70):
    try:
        img = Image.open(image_path)
        
        # Fix orientation
        img = fix_image_orientation(img)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
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

# ============================================
# 🔥 FIXED: Get Compressed Photo with Orientation Fix
# ============================================

def get_compressed_photo_b64(photo_field: str, serial_number: str = "") -> str | None:
    cache_key = f"compressed_{serial_number}_{photo_field}"
    if cache_key in st.session_state.photo_cache:
        return st.session_state.photo_cache[cache_key]

    # 1. Object Storage — primary source
    for key in filter(None, [photo_field, f"member_photos/{serial_number}.jpg" if serial_number else None]):
        try:
            b64, _ = object_store.get_photo_b64(key)
            if b64:
                # 🔥 Apply orientation fix on base64 image
                try:
                    img_bytes = base64.b64decode(b64)
                    img = Image.open(io.BytesIO(img_bytes))
                    img = fix_image_orientation(img)
                    
                    output = io.BytesIO()
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output, format='JPEG', quality=85, optimize=True)
                    fixed_b64 = base64.b64encode(output.getvalue()).decode()
                    result = f"data:image/jpeg;base64,{fixed_b64}"
                except:
                    result = f"data:image/jpeg;base64,{b64}"
                
                st.session_state.photo_cache[cache_key] = result
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
        compressed_data = compress_image(photo_path)
        if compressed_data:
            b64 = f"data:image/jpeg;base64,{base64.b64encode(compressed_data).decode()}"
            st.session_state.photo_cache[cache_key] = b64
            return b64

    return None

def get_member_with_photo(member, gym_name=""):
    photo_b64 = get_compressed_photo_b64(member.photo_path, member.serial_number)
    return {
        'id': member.id,
        'serial_number': member.serial_number,
        'full_name': member.full_name,
        'status': member.status,
        'membership_type': member.membership_type,
        'fee_amount': member.fee_amount,
        'join_date': member.join_date,
        'expiry_date': str(member.expiry_date) if member.expiry_date else None,
        'phone': member.phone,
        'gym_id': member.gym_id,
        'gym_name': gym_name,
        'photo_b64': photo_b64,
    }

# ============================================
# 🔥 FIXED: Card HTML with image-orientation:from-image
# ============================================

def render_card_html(member_data, gym_name: str, is_cached: bool = False, is_selected: bool = False) -> str:
    bg_clr, badge_clr = STATUS_COLORS.get(member_data.get('status'), ("#1E293B", "#94A3B8"))
    
    if is_selected:
        photo_width = 160
        photo_height = 220
    else:
        photo_width = 120
        photo_height = 180
    
    photo_b64 = member_data.get('photo_b64')
    
    if photo_b64:
        photo_html = f'''
        <div style="width:{photo_width}px; height:{photo_height}px; margin:0 auto 0.5rem;
                    border:3px solid #7C3AED; overflow:hidden;
                    background:#1E293B; border-radius:12px;
                    box-shadow:0 4px 15px rgba(124,58,237,0.3);
                    flex-shrink:0;">
            <img src="{photo_b64}" style="width:100%; height:100%;
                                          object-fit:cover; display:block;
                                          image-orientation:from-image;" />
        </div>
        '''
    else:
        photo_html = f'''
        <div style="width:{photo_width}px; height:{photo_height}px; margin:0 auto 0.5rem;
                    background:linear-gradient(135deg,#7C3AED,#A78BFA);
                    border:3px solid #7C3AED33; border-radius:12px;
                    display:flex; align-items:center; justify-content:center;
                    font-size:{photo_width//2}px; font-weight:700; color:#ffffff;
                    flex-shrink:0;">
            {member_data.get("full_name", "?")[0].upper()}
        </div>
        '''

    expiry_str = member_data.get('expiry_date') or "—"
    try:
        if expiry_str and expiry_str != "—":
            exp_d = date.fromisoformat(str(expiry_str))
            days_left = (exp_d - date.today()).days
            expiry_note = f"({days_left}d left)" if days_left >= 0 else "(EXPIRED)"
            exp_color = "#34D399" if days_left > 7 else "#FBBF24" if days_left >= 0 else "#F87171"
        else:
            expiry_note = ""
            exp_color = "#94A3B8"
    except:
        expiry_note = ""
        exp_color = "#94A3B8"

    cache_badge = ''
    if is_cached:
        cache_badge = '''
        <div style="text-align:center;margin-top:4px;">
            <span style="background:rgba(6,78,59,0.8);color:#34D399;
                        padding:2px 12px;border-radius:20px;
                        font-size:0.5rem;font-weight:600;
                        border:1px solid #34D39933;">
                CACHED
            </span>
        </div>
        '''

    fee = member_data.get('fee_amount') or 0
    try:
        fee_int = int(fee)
    except:
        fee_int = 0

    phone = member_data.get('phone') or ""
    name = member_data.get('full_name', 'Unknown')
    serial = member_data.get('serial_number', '---')
    membership = member_data.get('membership_type', '---')
    join_date = member_data.get('join_date', '---')
    status = member_data.get('status', 'UNKNOWN').upper()
    gym_display = gym_name or member_data.get('gym_name', 'GymPro')

    if is_selected:
        card_width = "380px"
        padding = "1.5rem"
        font_size = "0.95rem"
        border_radius = "18px"
        shadow = "0 12px 40px rgba(0,0,0,0.6)"
    else:
        card_width = "320px"
        padding = "1rem"
        font_size = "0.85rem"
        border_radius = "14px"
        shadow = "0 6px 25px rgba(0,0,0,0.5)"

    return f"""
    <div style="background:linear-gradient(145deg,#1E293B 0%,#0F172A 100%);
                border:1px solid #334155;border-radius:{border_radius};
                padding:{padding};max-width:{card_width};margin:0 auto;
                box-shadow:{shadow};
                position:relative;overflow:hidden;
                font-family:sans-serif;font-size:{font_size};">
        
        <div style="position:absolute;top:0;left:0;right:0;height:4px;
                    background:linear-gradient(90deg,#7C3AED,#A78BFA,#7C3AED);
                    box-shadow:0 0 20px rgba(124,58,237,0.3);"></div>
        
        <div style="position:absolute;top:-50px;right:-50px;width:100px;height:100px;
                    background:radial-gradient(circle,rgba(124,58,237,0.1),transparent);
                    border-radius:50%;"></div>
        <div style="position:absolute;bottom:-50px;left:-50px;width:100px;height:100px;
                    background:radial-gradient(circle,rgba(124,58,237,0.05),transparent);
                    border-radius:50%;"></div>
        
        <div style="text-align:center;margin-bottom:0.4rem;position:relative;z-index:1;">
            <div style="font-size:0.5rem;color:#64748B;letter-spacing:0.15em;
                        text-transform:uppercase;font-weight:600;">
                GymPro Multi-Gym
            </div>
            <div style="font-size:0.8rem;font-weight:700;color:#A78BFA;
                        margin-top:0.05rem;letter-spacing:0.05em;">
                {gym_display}
            </div>
        </div>
        
        {photo_html}
        
        <div style="text-align:center;margin-bottom:0.4rem;position:relative;z-index:1;">
            <div style="font-size:{1.1 if is_selected else 0.9}rem;
                        font-weight:700;color:#E2E8F0;
                        text-shadow:0 2px 10px rgba(0,0,0,0.3);">
                {name}
            </div>
            <div style="font-size:0.65rem;color:#7C3AED;font-weight:600;
                        letter-spacing:0.08em;font-family:monospace;
                        background:rgba(124,58,237,0.1);
                        padding:0.1rem 0.5rem;border-radius:4px;
                        display:inline-block;margin-top:0.1rem;">
                {serial}
            </div>
        </div>
        
        <div style="text-align:center;margin-bottom:0.4rem;position:relative;z-index:1;">
            <span style="background:{bg_clr};color:{badge_clr};
                        padding:0.15rem 1rem;border-radius:9999px;
                        font-size:0.6rem;font-weight:600;letter-spacing:0.05em;
                        border:1px solid {badge_clr}33;
                        box-shadow:0 2px 8px rgba(0,0,0,0.2);">
                {status}
            </span>
        </div>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.3rem;
                    margin-bottom:0.4rem;position:relative;z-index:1;">
            <div style="background:rgba(15,23,42,0.8);border-radius:8px;
                        padding:0.3rem;border:1px solid rgba(51,65,85,0.5);">
                <div style="font-size:0.45rem;color:#64748B;text-transform:uppercase;
                            letter-spacing:0.06em;font-weight:600;">Membership</div>
                <div style="font-size:0.7rem;font-weight:600;color:#E2E8F0;">{membership}</div>
            </div>
            <div style="background:rgba(15,23,42,0.8);border-radius:8px;
                        padding:0.3rem;border:1px solid rgba(51,65,85,0.5);">
                <div style="font-size:0.45rem;color:#64748B;text-transform:uppercase;
                            letter-spacing:0.06em;font-weight:600;">Fee</div>
                <div style="font-size:0.7rem;font-weight:600;color:#34D399;">PKR {fee_int:,.0f}</div>
            </div>
            <div style="background:rgba(15,23,42,0.8);border-radius:8px;
                        padding:0.3rem;border:1px solid rgba(51,65,85,0.5);">
                <div style="font-size:0.45rem;color:#64748B;text-transform:uppercase;
                            letter-spacing:0.06em;font-weight:600;">Join</div>
                <div style="font-size:0.65rem;font-weight:600;color:#E2E8F0;">{join_date}</div>
            </div>
            <div style="background:rgba(15,23,42,0.8);border-radius:8px;
                        padding:0.3rem;border:1px solid rgba(51,65,85,0.5);">
                <div style="font-size:0.45rem;color:#64748B;text-transform:uppercase;
                            letter-spacing:0.06em;font-weight:600;">Expiry</div>
                <div style="font-size:0.65rem;font-weight:600;color:{exp_color};">{expiry_str} <span style="font-size:0.5rem;">{expiry_note}</span></div>
            </div>
        </div>
        
        {f'<div style="text-align:center;font-size:0.6rem;color:#64748B;margin-bottom:0.2rem;position:relative;z-index:1;">{phone}</div>' if phone else ''}
        
        {cache_badge}
        
        {'' if is_selected else '<div style="text-align:center;font-size:0.4rem;color:#64748B;margin-top:0.2rem;opacity:0.5;">Click Select to view details</div>'}
    </div>
    """

def recompress_all_images():
    if not os.path.exists(UPLOAD_DIR):
        return 0
    
    fixed_count = 0
    for file_name in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            try:
                compressed = compress_image(file_path)
                if compressed:
                    with open(file_path, 'wb') as f:
                        f.write(compressed)
                    fixed_count += 1
            except:
                pass
    
    return fixed_count

def render(gym_id, role):
    init_session_state()
    
    styles.page_header("Membership Cards", "Digital Identity Verification - Member Photo ID Preview")
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True)
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("Gym Location", list(opts.keys()))
            sel_gid = opts[chosen]
            
    with fc2:
        search = st.text_input("Search Member", placeholder="Name, serial, phone")
    with fc3:
        status_f = st.selectbox("Status", ["All", "Active", "Inactive", "Suspended", "Frozen"])

    members = db.get_members(gym_id=sel_gid, status=status_f, search=search)
    if not members:
        st.info("No members match your filters.")
        return

    st.markdown(f"**{len(members)} member card(s)**")
    st.divider()

    with st.expander("Photo Tools", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fix All Image Orientations", use_container_width=True):
                with st.spinner("Fixing all images..."):
                    count = recompress_all_images()
                    st.session_state.photo_cache = {}
                    st.session_state.gallery_loaded = False
                    st.session_state.gallery_html = []
                    st.success(f"Fixed {count} images!")
                    st.rerun()
        with col2:
            if st.button("Clear All Cache", use_container_width=True):
                try:
                    if os.path.exists(CACHE_FILE):
                        os.remove(CACHE_FILE)
                    if os.path.exists(GALLERY_CACHE_FILE):
                        os.remove(GALLERY_CACHE_FILE)
                    st.session_state.photo_cache = {}
                    st.session_state.gallery_loaded = False
                    st.session_state.gallery_html = []
                    st.session_state.all_members_data = []
                    st.success("Cache cleared!")
                    st.rerun()
                except:
                    pass

    need_rebuild = (
        not st.session_state.gallery_loaded or 
        st.session_state._member_count != len(members) or
        len(st.session_state.gallery_html) != len(members)
    )
    
    if need_rebuild:
        all_members_data = []
        for m in members:
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "GymPro")
            member_data = get_member_with_photo(m, gym_name)
            all_members_data.append(member_data)
        
        gallery_html_parts = []
        for md in all_members_data:
            is_cached = False
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r") as f:
                        cached = json.load(f)
                        if cached.get('id') == md.get('id'):
                            is_cached = True
                except:
                    pass
            card_html = render_card_html(md, md.get('gym_name', 'GymPro'), is_cached, is_selected=False)
            gallery_html_parts.append(card_html)
        
        st.session_state.gallery_html = gallery_html_parts
        st.session_state.all_members_data = all_members_data
        st.session_state.gallery_loaded = True
        st.session_state._member_count = len(members)
        
        try:
            cache_data = {
                'members': all_members_data,
                '_count': len(members),
                '_cached_at': datetime.now().isoformat()
            }
            with open(GALLERY_CACHE_FILE, "w") as f:
                json.dump(cache_data, f, default=str)
        except:
            pass

    cached_selected = None
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cached_selected = json.load(f)
    except:
        pass
    
    default_index = 0
    if cached_selected:
        cached_id = cached_selected.get('id')
        for idx, m in enumerate(members):
            if m.id == cached_id:
                default_index = idx
                break
    
    mem_opts = {f"{m.serial_number} - {m.full_name}": m.id for m in members}
    mem_labels = list(mem_opts.keys())
    
    selected_label = st.selectbox(
        "Select member to preview card", 
        mem_labels,
        index=default_index if default_index < len(mem_labels) else 0
    )
    
    selected_mid = mem_opts[selected_label]
    selected_m = next((m for m in members if m.id == selected_mid), None)
    
    if not selected_m:
        return
    
    if not cached_selected or cached_selected.get('id') != selected_m.id:
        cache_data = {
            'id': selected_m.id,
            'serial_number': selected_m.serial_number,
            'full_name': selected_m.full_name,
            'status': selected_m.status,
            'membership_type': selected_m.membership_type,
            'fee_amount': selected_m.fee_amount,
            'join_date': selected_m.join_date,
            'expiry_date': str(selected_m.expiry_date) if selected_m.expiry_date else None,
            'phone': selected_m.phone,
            'photo_path': selected_m.photo_path,
        }
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(cache_data, f, default=str)
        except:
            pass
    
    selected_data = None
    for md in st.session_state.all_members_data:
        if md.get('id') == selected_m.id:
            selected_data = md
            break
    
    if not selected_data:
        gym_name = next((g.name for g in gyms if g.id == selected_m.gym_id), "GymPro")
        selected_data = get_member_with_photo(selected_m, gym_name)
    
    is_cached = cached_selected and cached_selected.get('id') == selected_m.id
    
    col_card, col_info = st.columns([1, 1])
    
    with col_card:
        st.markdown("Membership Card Preview")
        if is_cached:
            st.success("Loaded from cache")
        else:
            st.info("Fresh from database")
        
        st.components.v1.html(
            render_card_html(selected_data, selected_data.get('gym_name', 'GymPro'), is_cached, is_selected=True),
            height=600,
            scrolling=False
        )
    
    with col_info:
        st.markdown("Digital Identity Details")
        st.markdown(f"""
| Field | Value |
|-------|-------|
| **Full Name** | {selected_m.full_name} |
| **Serial No.** | {selected_m.serial_number} |
| **Membership** | {selected_m.membership_type} |
| **Status** | {selected_m.status} |
| **Cache** | {'Cached' if is_cached else 'Fresh'} |
        """)
        
        st.markdown("Update Identity Image")
        new_photo = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"], key=f"upload_{selected_m.id}")
        
        if new_photo:
            ext = os.path.splitext(new_photo.name)[-1].lower()
            clean_s = str(selected_m.serial_number).strip().replace("-", "").lower()
            new_filename = f"{clean_s}{ext}"
            path = os.path.join(UPLOAD_DIR, new_filename)
            
            img = Image.open(new_photo)
            img = fix_image_orientation(img)
            
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            max_width = 400
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            img.save(path, 'JPEG', quality=70, optimize=True)
            
            db.update_member(
                selected_m.id,
                photo_path=f"gym-app/uploads/{new_filename}",
                full_name=selected_m.full_name,
                phone=selected_m.phone or "",
                email=selected_m.email or "",
                gender=selected_m.gender or "",
                dob=selected_m.dob or "",
                membership_type=selected_m.membership_type,
                fee_amount=selected_m.fee_amount or 0,
                join_date=selected_m.join_date,
                expiry_date=selected_m.expiry_date or "",
                status=selected_m.status,
                notes=selected_m.notes or "",
            )
            st.session_state.photo_cache = {}
            st.session_state.gallery_loaded = False
            st.session_state.gallery_html = []
            st.session_state.all_members_data = []
            if os.path.exists(GALLERY_CACHE_FILE):
                os.remove(GALLERY_CACHE_FILE)
            st.success("Photo updated!")
            st.rerun()
    
    st.write("")
    with st.expander(f"View All {len(members)} Cards (Gallery View)", expanded=False):
        st.caption(f"All {len(members)} cards - Click Select to view details")
        
        gallery_html_parts = st.session_state.gallery_html
        
        if gallery_html_parts:
            cols = st.columns(3)
            for idx, card_html in enumerate(gallery_html_parts):
                if idx >= len(members):
                    break
                with cols[idx % 3]:
                    member_id = members[idx].id
                    if st.button(
                        "Select", 
                        key=f"select_card_{member_id}",
                        use_container_width=True,
                        help="Click to view this member's full card"
                    ):
                        cache_data = {
                            'id': member_id,
                            'serial_number': members[idx].serial_number,
                            'full_name': members[idx].full_name,
                            'status': members[idx].status,
                            'membership_type': members[idx].membership_type,
                            'fee_amount': members[idx].fee_amount,
                            'join_date': members[idx].join_date,
                            'expiry_date': str(members[idx].expiry_date) if members[idx].expiry_date else None,
                            'phone': members[idx].phone,
                            'photo_path': members[idx].photo_path,
                        }
                        try:
                            with open(CACHE_FILE, "w") as f:
                                json.dump(cache_data, f, default=str)
                        except:
                            pass
                        st.rerun()
                    
                    st.components.v1.html(card_html, height=500, scrolling=False)
        else:
            st.warning("No gallery data available.")