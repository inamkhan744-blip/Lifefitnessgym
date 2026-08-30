"""Safe, admin-controlled visual design selector.

Only the existing app_settings preference is written here.  No member,
payment, attendance, gym, photo, or other business data is touched.
"""

import streamlit as st

import database as db
import themes


def render():
    st.markdown(
        """
        <div class="settings-hero">
          <div class="dash-eyebrow">WORKSPACE PREFERENCES</div>
          <h1>Settings & design system</h1>
          <p>Choose a complete GymPro interface. Your records, IDs, photos and permissions stay unchanged.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current = themes.current_theme()
    st.markdown("### Choose your GymPro experience")
    st.caption("Each option changes navigation, spacing, typography, cards and dashboard composition across the application.")
    options = list(themes.DESIGN_THEMES.keys())
    labels = [themes.THEME_NAMES[k] for k in options]

    cols = st.columns(2)
    for index, (key, label) in enumerate(zip(options, labels), start=1):
        spec = themes.DESIGN_THEMES[key]
        with cols[(index - 1) % 2]:
            selected = " selected" if key == current else ""
            st.markdown(
                f"""
                <div class="design-option design-option-{index}{selected}">
                  <div class="design-swatch">
                    <span style="background:{spec["accent"]}"></span>
                    <span style="background:{spec["accent2"]}"></span>
                    <span style="background:{spec["surface"]}"></span>
                  </div>
                  <div>
                    <div class="design-number">DESIGN {index:02d}</div>
                    <h3>{label}</h3>
                    <p>{spec["description"]}</p>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Currently active" if key == current else f"Use Design {index}",
                key=f"settings_design_{key}",
                type="primary" if key == current else "secondary",
                use_container_width=True,
                disabled=key == current,
            ):
                db.set_setting("theme_key", key)
                db.set_setting("theme_auto", "0")
                st.cache_data.clear()
                st.session_state["current_theme"] = key
                st.success(f"{label} is now active.")
                st.rerun()

    st.divider()
    st.markdown("### Data safety status")
    c1, c2, c3 = st.columns(3)
    c1.metric("Database mode", db.DB_MODE.title())
    c2.metric("Current design", f"Design {options.index(current) + 1}")
    c3.metric("Data changes", "None")
    st.info("Theme selection only updates the existing app_settings preference. It does not migrate or rewrite the database.")