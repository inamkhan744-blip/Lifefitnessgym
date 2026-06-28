---
name: Streamlit quirks
description: Known Streamlit version-specific gotchas in this project
---

# Streamlit Quirks (v1.57)

## Empty radio label warning
`st.radio(label="", ...)` raises an accessibility warning in Streamlit 1.45+. 
**Fix:** Always supply a real label string + `label_visibility="collapsed"` to hide it visually.

## use_container_width deprecation
`use_container_width=True` → use `width='stretch'` after 2025-12-31.
`use_container_width=False` → use `width='content'`.
Currently still works but logs warnings — migrate when doing major UI passes.
