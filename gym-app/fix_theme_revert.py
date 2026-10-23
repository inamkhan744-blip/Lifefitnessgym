import re

# 1. Fix app.py (Sidebar Logic)
path_app = "app.py"
with open(path_app, "r") as f:
    app_content = f.read()

# Purana block jo selectbox render kar raha tha
old_sidebar = '''        if not _auto_toggle:
            _all_labels = list(themes.THEME_NAMES.values())
            _all_keys   = list(themes.THEME_NAMES.keys())
            _sel_idx    = _all_keys.index(_cur_key) if _cur_key in _all_keys else 0
            _picked     = st.selectbox(
                "Select Theme",
                _all_labels,
                index=_sel_idx,
                key="theme_picker",
                label_visibility="collapsed",
            )
            _picked_key = _all_keys[_all_labels.index(_picked)]
            if _picked_key != _cur_key:
                db.set_setting("theme_key", _picked_key)
                st.rerun()
        else:
            st.caption(f"Today: **{_cur_label}**")'''

# Naya block jo session state ko force sync karega
new_sidebar = '''        if not _auto_toggle:
            _all_labels = list(themes.THEME_NAMES.values())
            _all_keys   = list(themes.THEME_NAMES.keys())
            _expected_label = themes.THEME_NAMES.get(_cur_key, _all_labels[0])
            
            # 🔥 FIX: Force sync session state with database
            if "theme_picker" not in st.session_state or st.session_state["theme_picker"] != _expected_label:
                st.session_state["theme_picker"] = _expected_label

            _picked     = st.selectbox(
                "Select Theme",
                _all_labels,
                key="theme_picker",
                label_visibility="collapsed",
            )
            _picked_key = _all_keys[_all_labels.index(_picked)]
            if _picked_key != _cur_key:
                db.set_setting("theme_key", _picked_key)
                st.rerun()
        else:
            st.caption(f"Today: **{_cur_label}**")'''

if old_sidebar in app_content:
    app_content = app_content.replace(old_sidebar, new_sidebar)
    with open(path_app, "w") as f:
        f.write(app_content)
    print("✅ Fixed app.py sidebar synchronization!")
else:
    print("⚠️ app.py mein sidebar block thoda different hai, but trying regex...")
    # Fallback agar upar wala exactly match na ho
    pattern = re.compile(r'        if not _auto_toggle:.*?st\.caption\(f"Today: \*\*\{_cur_label\}\*\*"\)', re.DOTALL)
    app_content = pattern.sub(new_sidebar, app_content)
    with open(path_app, "w") as f:
        f.write(app_content)
    print("✅ Applied regex fix for app.py!")

# 2. Update settings.py to also sync session_state immediately
path_settings = "gym_pages/settings.py"
with open(path_settings, "r") as f:
    settings_content = f.read()

# Add session_state sync in settings.py before st.rerun()
old_apply = '''                        db.set_setting("theme_key", key)
                        db.set_setting("theme_auto", "0")
                        st.session_state["current_theme"] = key
                        st.session_state["_gympro_theme"] = key
                        
                        # Clear ALL possible caches
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        
                        st.session_state["theme_applied_msg"] = f"🎨 {spec['name']} successfully apply ho gaya!"
                        time.sleep(0.5)
                        st.rerun()'''

new_apply = '''                        db.set_setting("theme_key", key)
                        db.set_setting("theme_auto", "0")
                        st.session_state["current_theme"] = key
                        st.session_state["_gympro_theme"] = key
                        st.session_state["theme_picker"] = spec['emoji'] + " " + spec['name'] # Force sidebar match
                        
                        # Clear ALL possible caches
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        
                        st.session_state["theme_applied_msg"] = f"🎨 {spec['name']} successfully apply ho gaya!"
                        time.sleep(0.5)
                        st.rerun()'''

if old_apply in settings_content:
    settings_content = settings_content.replace(old_apply, new_apply)
    with open(path_settings, "w") as f:
        f.write(settings_content)
    print("✅ Fixed settings.py to force sidebar update!")
else:
    print("ℹ️ settings.py apply block not exactly matched, but main fix is in app.py")
