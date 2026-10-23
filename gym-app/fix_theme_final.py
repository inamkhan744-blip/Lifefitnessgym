import re

# 1. Fix app.py caching
path_app = "app.py"
with open(path_app, "r") as f:
    app_content = f.read()

# Remove the cache decorator from _cached_theme_settings
if "@st.cache_data(ttl=300, show_spinner=False)\ndef _cached_theme_settings():" in app_content:
    app_content = app_content.replace(
        "@st.cache_data(ttl=300, show_spinner=False)\ndef _cached_theme_settings():",
        "def _cached_theme_settings():"
    )
    with open(path_app, "w") as f:
        f.write(app_content)
    print("✅ Fixed app.py theme cache issue!")

# 2. Update settings.py to show more details and fix button
path_settings = "gym_pages/settings.py"
with open(path_settings, "r") as f:
    settings_content = f.read()

new_settings = '''"""
GymPro Settings & Theme Selector v3.1 - CACHE FIXED
Live Theme Previews, General Settings, and System Tools.
"""

import streamlit as st
import database as db
import themes
import time

def render():
    st.markdown(
        """
        <div class="settings-hero">
          <div class="dash-eyebrow">WORKSPACE PREFERENCES</div>
          <h1>Settings & Design System</h1>
          <p>Apni pasand ka design chunein, app ki settings change karein aur system check karein.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show success message after reload
    if st.session_state.get("theme_applied_msg"):
        st.success(st.session_state["theme_applied_msg"])
        st.session_state["theme_applied_msg"] = None

    # 3 Main Tabs
    tab_themes, tab_general, tab_system = st.tabs(["🎨 Themes & Design", "⚙️ General Settings", "🛡️ System & Safety"])

    # ═══════════════════════════════════════════════════════════
    # TAB 1: THEMES
    # ═══════════════════════════════════════════════════════════
    with tab_themes:
        current_key = themes.current_theme()
        
        # Categories
        categories = {
            "☀️ Light & Fresh": [k for k in themes.THEME_KEYS if 1 <= int(k.split('_')[1]) <= 15],
            "🌙 Dark & Premium": [k for k in themes.THEME_KEYS if 16 <= int(k.split('_')[1]) <= 25],
            "⚡ Cyber & Tech": [k for k in themes.THEME_KEYS if 26 <= int(k.split('_')[1]) <= 30],
            "🌿 Nature": [k for k in themes.THEME_KEYS if 31 <= int(k.split('_')[1]) <= 38],
            "👑 Luxury": [k for k in themes.THEME_KEYS if 39 <= int(k.split('_')[1]) <= 45],
        }

        selected_cat = st.selectbox("Theme Category Chunein", list(categories.keys()))
        st.markdown(f"#### {selected_cat} Themes")
        st.caption("Niche diye gaye preview mein dekhein ke theme kaisi lagegi, phir Apply dabayein.")
        st.divider()

        # Display Themes in a Grid (2 columns for mobile compatibility)
        keys_to_show = categories[selected_cat]
        cols = st.columns(2)
        
        for idx, key in enumerate(keys_to_show):
            spec = themes.DESIGN_THEMES[key]
            is_active = (key == current_key)
            
            with cols[idx % 2]:
                # Detailed HTML Preview Card
                st.markdown(f"""
                <div style="background: {spec['bg_gradient']}; border-radius: 12px; padding: 15px; border: 2px solid {spec['accent'] if is_active else 'rgba(0,0,0,0.1)'}; margin-bottom: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <div style="color: {spec['text']}; font-size: 16px; font-weight: 800; margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.2);">
                        {spec['emoji']} {spec['name']}
                    </div>
                    <div style="color: {spec['muted']}; font-size: 11px; margin-bottom: 12px;">
                        {spec['description']}
                    </div>
                    <!-- Mini Fake UI -->
                    <div style="background: {spec['surface']}; border-radius: 8px; padding: 8px; backdrop-filter: blur(10px); border: 1px solid {spec['border']};">
                        <div style="color: {spec['text']}; font-size: 10px; margin-bottom: 5px;">Sample Text</div>
                        <div style="background: {spec['btn_gradient']}; color: #FFF; text-align: center; border-radius: 4px; padding: 4px; font-size: 10px; font-weight: bold; box-shadow: {spec['btn_shadow']};">
                            Sample Button
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if is_active:
                    st.button("✅ Active", key=f"act_{key}", disabled=True, use_container_width=True)
                else:
                    if st.button(f"Apply Theme", key=f"apply_{key}", type="primary", use_container_width=True):
                        # 🔥 FORCE APPLY
                        db.set_setting("theme_key", key)
                        db.set_setting("theme_auto", "0")
                        st.session_state["current_theme"] = key
                        st.session_state["_gympro_theme"] = key
                        
                        # Clear ALL possible caches
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        
                        st.session_state["theme_applied_msg"] = f"🎨 {spec['name']} successfully apply ho gaya!"
                        time.sleep(0.5)
                        st.rerun()

    # ═══════════════════════════════════════════════════════════
    # TAB 2: GENERAL SETTINGS
    # ═══════════════════════════════════════════════════════════
    with tab_general:
        st.markdown("### 🏢 App ki Aam Settings")
        st.caption("Ye settings poori app aur receipts par asar dalti hain.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏋️ Business Name")
            current_gym_name = db.get_setting("gym_display_name", "LIFE FITNESS GYM")
            new_gym_name = st.text_input("App Display Name", value=current_gym_name, help="Ye naam loading screen aur dashboard par dikhega.")
            if st.button("💾 Save Name", use_container_width=True):
                db.set_setting("gym_display_name", new_gym_name)
                st.success("✅ Business Name updated!")
                st.rerun()

        with col2:
            st.markdown("#### 💰 Currency Symbol")
            curr_opts = ["PKR", "INR", "USD", "AED", "SAR", "GBP"]
            current_curr = db.get_setting("currency_symbol", "PKR")
            idx = curr_opts.index(current_curr) if current_curr in curr_opts else 0
            new_curr = st.selectbox("Select Currency", curr_opts, index=idx)
            if st.button("💾 Save Currency", use_container_width=True):
                db.set_setting("currency_symbol", new_curr)
                st.success(f"✅ Currency updated to {new_curr}!")
                st.rerun()

        st.divider()
        
        # Naya Feature: Receipt Footer
        st.markdown("#### 🧾 Receipt Footer Note")
        current_note = db.get_setting("receipt_footer", "Thank you for choosing us! Stay Fit 💪")
        new_note = st.text_area("Footer Message (Jo receipt ke neeche aayega)", value=current_note, height=80)
        if st.button("💾 Save Receipt Note", use_container_width=True):
            db.set_setting("receipt_footer", new_note)
            st.success("✅ Receipt note saved!")
            st.rerun()

        st.divider()
        st.markdown("#### 🎨 Auto Daily Theme")
        auto_on = db.get_setting("theme_auto", "0") == "1"
        if st.toggle("Roz naya theme lagao (Auto Change)", value=auto_on):
            if not auto_on:
                db.set_setting("theme_auto", "1")
                st.rerun()
        else:
            if auto_on:
                db.set_setting("theme_auto", "0")
                st.rerun()

    # ═══════════════════════════════════════════════════════════
    # TAB 3: SYSTEM & SAFETY
    # ═══════════════════════════════════════════════════════════
    with tab_system:
        st.markdown("### 🛡️ System Status & Safety")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Database Mode", db.DB_MODE.title())
        c2.metric("Active Theme", themes.THEME_NAMES.get(current_key, "Unknown"))
        c3.metric("Data Safety", "100% Secure")
        
        st.info("Aapka saara data Neon Database (Cloud) mein mehfooz hai. Settings change karne se aapka data kabhi delete ya kharab nahi hota.")
        
        st.divider()
        
        st.markdown("#### 🧹 Cache & Optimization")
        st.caption("Agar app purana data dikha rahi hai ya atak rahi hai, to cache clear karein.")
        
        if st.button("🔄 Clear App Cache & Reload", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache clear ho gaya! App restart ho rahi hai...")
            time.sleep(1)
            st.rerun()
            
        st.divider()
        st.markdown("#### ℹ️ App Info")
        st.markdown("""
        * **App Name:** GymPro AI
        * **Version:** 31.0.0 (Masterpiece)
        * **Developer:** Inam Khan
        * **Powered By:** Streamlit, Python, Neon DB
        """)
'''

with open(path_settings, "w") as f:
    f.write(new_settings)
print("✅ Updated settings.py with detailed previews and cache fix!")
