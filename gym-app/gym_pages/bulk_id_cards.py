"""
Bulk ID Card Generator — Admin only
Multiple members ke cards ek saath PDF ya ZIP mein download karo
"""
import io
import zipfile
import streamlit as st
import database as db
import id_card
import styles


def render(gym_id, role):
    styles.page_header("🖨️", "Bulk ID Cards", "Select members and download ID cards in bulk")

    if role not in ("admin", "staff"):
        st.warning("🔒 Access denied.")
        return

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Pehle Gym Setup mein gym add karein.")
        return

    # ── Gym selector ─────────────────────────────────────────────────
    gym_opts = {g.name: g.id for g in gyms}
    default_name = next((g.name for g in gyms if g.id == gym_id), list(gym_opts.keys())[0])
    selected_gym_name = st.selectbox("Gym", list(gym_opts.keys()),
                                     index=list(gym_opts.keys()).index(default_name),
                                     key="bulk_gym_sel")
    sel_gym_id = gym_opts[selected_gym_name]

    members = db.get_members(gym_id=sel_gym_id)
    if not members:
        st.info("Is gym mein koi member nahi hai.")
        return

    # ── Filters ──────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        status_f = st.selectbox("Status filter", ["All", "Active", "Inactive", "Suspended", "Frozen"],
                                key="bulk_status")
    with fc2:
        mem_type_f = st.selectbox("Membership type",
                                  ["All"] + sorted({m.membership_type for m in members
                                                    if m.membership_type}),
                                  key="bulk_memtype")
    with fc3:
        search_q = st.text_input("Search by name/serial", key="bulk_search",
                                 placeholder="Type to filter…")

    # Apply filters
    filtered = members
    if status_f != "All":
        filtered = [m for m in filtered if (m.status or "").lower() == status_f.lower()]
    if mem_type_f != "All":
        filtered = [m for m in filtered if m.membership_type == mem_type_f]
    if search_q:
        q = search_q.strip().lower()
        filtered = [m for m in filtered
                    if q in (m.full_name or "").lower()
                    or q in (m.serial_number or "").lower()]

    if not filtered:
        st.warning("Filter se koi member nahi mila.")
        return

    st.markdown(f"**{len(filtered)} members** is filter mein")

    # ── Member selection ──────────────────────────────────────────────
    st.markdown("---")

    col_sa, col_sn = st.columns([1, 4])
    with col_sa:
        if st.button("✅ Select All", use_container_width=True):
            for m in filtered:
                st.session_state[f"bulk_sel_{m.id}"] = True
    with col_sn:
        if st.button("❌ Deselect All", use_container_width=True):
            for m in filtered:
                st.session_state[f"bulk_sel_{m.id}"] = False

    # Checkboxes — 3 per row
    cols_per_row = 3
    for i in range(0, len(filtered), cols_per_row):
        row_members = filtered[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, m in zip(cols, row_members):
            with col:
                label = f"**{m.serial_number}** — {m.full_name}"
                st.session_state.setdefault(f"bulk_sel_{m.id}", False)
                st.checkbox(label, key=f"bulk_sel_{m.id}")

    selected = [m for m in filtered if st.session_state.get(f"bulk_sel_{m.id}", False)]
    st.markdown(f"**{len(selected)} selected**")

    if not selected:
        st.info("Upar checkboxes mein members choose karein.")
        return

    # ── Generate buttons ─────────────────────────────────────────────
    st.markdown("---")
    g1, g2 = st.columns(2)

    with g1:
        if st.button(f"📄 Generate Multi-Page PDF ({len(selected)} cards)",
                     type="primary", use_container_width=True):
            _generate_pdf(selected, selected_gym_name)

    with g2:
        if st.button(f"🗜️ Generate ZIP of PNGs ({len(selected)} cards)",
                     use_container_width=True):
            _generate_zip(selected, selected_gym_name)


# ─── PDF generation ──────────────────────────────────────────────────────────

def _generate_pdf(members_list, gym_name: str):
    progress_bar = st.progress(0, text="Cards generate ho rahi hain…")
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        import io as _io

        buf = _io.BytesIO()
        page_w, page_h = A4
        c = rl_canvas.Canvas(buf, pagesize=A4)

        total = len(members_list)
        for idx, member in enumerate(members_list):
            progress_bar.progress((idx) / total,
                                  text=f"Card {idx+1}/{total}: {member.full_name}…")
            try:
                png_bytes = id_card.generate_id_card_png(member, gym_name)
                img_reader = ImageReader(_io.BytesIO(png_bytes))

                card_pdf_w = page_w - 80
                card_pdf_h = card_pdf_w * (id_card.CARD_H / id_card.CARD_W)
                x = (page_w - card_pdf_w) / 2
                y = (page_h - card_pdf_h) / 2

                c.drawImage(img_reader, x, y,
                            width=card_pdf_w, height=card_pdf_h,
                            preserveAspectRatio=True)

                # Cut marks
                c.setDash(3, 3)
                c.setStrokeColorRGB(0.7, 0.7, 0.7)
                c.setLineWidth(0.5)
                m_pad = 8
                c.rect(x - m_pad, y - m_pad,
                       card_pdf_w + 2*m_pad, card_pdf_h + 2*m_pad)
                c.setDash()

                # Page number footer
                c.setFont("Helvetica", 8)
                c.setFillColorRGB(0.6, 0.6, 0.6)
                c.drawCentredString(page_w / 2, 20,
                                    f"{member.serial_number} — {member.full_name}  ({idx+1}/{total})")

            except Exception as e:
                # Blank page with error note if one card fails
                c.setFont("Helvetica", 10)
                c.setFillColorRGB(0.8, 0.2, 0.2)
                c.drawCentredString(page_w/2, page_h/2,
                                    f"Error for {member.serial_number}: {e}")

            c.showPage()

        c.save()
        progress_bar.progress(1.0, text="✅ PDF ready!")

        st.download_button(
            label=f"⬇️ Download PDF ({total} cards)",
            data=buf.getvalue(),
            file_name=f"{gym_name}_id_cards_bulk.pdf",
            mime="application/pdf",
            key="bulk_pdf_dl",
            type="primary",
            use_container_width=True,
        )

    except Exception as e:
        progress_bar.empty()
        st.error(f"PDF generation failed: {e}")


# ─── ZIP generation ──────────────────────────────────────────────────────────

def _generate_zip(members_list, gym_name: str):
    progress_bar = st.progress(0, text="Cards generate ho rahi hain…")
    try:
        zip_buf = io.BytesIO()
        total = len(members_list)

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, member in enumerate(members_list):
                progress_bar.progress(idx / total,
                                      text=f"Card {idx+1}/{total}: {member.full_name}…")
                try:
                    png_bytes = id_card.generate_id_card_png(member, gym_name)
                    fname = f"{member.serial_number}_{member.full_name.replace(' ', '_')}_id_card.png"
                    zf.writestr(fname, png_bytes)
                except Exception as e:
                    zf.writestr(f"{member.serial_number}_ERROR.txt", str(e))

        progress_bar.progress(1.0, text="✅ ZIP ready!")

        st.download_button(
            label=f"⬇️ Download ZIP ({total} PNGs)",
            data=zip_buf.getvalue(),
            file_name=f"{gym_name}_id_cards_bulk.zip",
            mime="application/zip",
            key="bulk_zip_dl",
            use_container_width=True,
        )

    except Exception as e:
        progress_bar.empty()
        st.error(f"ZIP generation failed: {e}")
