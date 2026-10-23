import re

path = "app.py"
with open(path, "r") as f:
    content = f.read()

# Purana kharab block dhoondein
pattern = re.compile(r'        _auto_toggle = st\.checkbox\("Auto \(daily\)".*?st\.caption\(f"Today: \*\*\{_cur_label\}\*\*"\)', re.DOTALL)

# Naya perfect block (bina kisi cache error ke)
new_block = '''        _auto_toggle = st.checkbox("Auto (daily)", value=_auto_on, key="theme_auto_chk")
        if _auto_toggle != _auto_on:
            db.set_setting("theme_auto", "1" if _auto_toggle else "0")
            st.rerun()

        if not _auto_toggle:
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

if pattern.search(content):
    content = pattern.sub(new_block, content)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Indentation fixed perfectly! App will run now.")
else:
    # Agar exact match na mile to line by line fix karein
    lines = content.split('\n')
    for i in range(len(lines)):
        if "st.rerun()" in lines[i] and "def " not in lines[i]:
            # Check if this is the line causing the error
            if i > 0 and "_cached_theme_settings" in lines[i-2]:
                lines[i] = "            st.rerun()"
    with open(path, "w") as f:
        f.write('\n'.join(lines))
    print("✅ Applied safety fix for indentation!")
