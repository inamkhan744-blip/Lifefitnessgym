"""
printer_utils.py
================
Browser-based 80mm thermal receipt printing for Streamlit.
No CUPS, no system commands — works on any device (mobile, desktop).
"""

from datetime import datetime

W = 32  # 80mm thermal = 32 usable chars at standard font

# WhatsApp Complaint Number
WHATSAPP_NUMBER = "03458308886"


# ── Text Formatting Helpers ────────────────────────────────────────────────────

def _line(char="="):
    return char * W

def _center(text, width=W):
    text = str(text)[:width]
    return text.center(width)

def _left_right(left, right, width=W):
    left = str(left)
    right = str(right)
    gap = width - len(left) - len(right)
    if gap < 1:
        gap = 1
        left = left[:width - len(right) - 1]
    return left + " " * gap + right

def _wrap(text, width=W):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= width:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word[:width]
    if current:
        lines.append(current)
    return lines or [""]


# ── Receipt Text Formatter ─────────────────────────────────────────────────────

def format_receipt(data: dict, copy_label: str = "MEMBER COPY") -> str:
    gym_name    = str(data.get("gym_name",    "GYM CENTER"))[:W]
    gym_addr    = str(data.get("gym_address", ""))[:W]
    gym_phone   = str(data.get("gym_phone",   ""))[:W]
    receipt_no  = str(data.get("receipt_no",  "N/A"))
    pay_date    = str(data.get("date",        datetime.now().strftime("%Y-%m-%d")))
    pay_time    = str(data.get("time",        datetime.now().strftime("%I:%M %p")))
    collected   = str(data.get("collected_by","Staff"))[:16]
    member_name = str(data.get("member_name", "N/A"))
    serial      = str(data.get("serial",      "N/A"))
    phone       = str(data.get("phone",       "N/A"))
    amount      = data.get("amount", 0)
    method      = str(data.get("method",      "Cash"))
    p_start     = str(data.get("period_start","N/A"))
    p_end       = str(data.get("period_end",  "N/A"))

    try:
        amount_str = f"PKR {float(amount):,.2f}"
    except Exception:
        amount_str = str(amount)

    lines = []
    a = lines.append
    
    # 🔥 NO EMOJIS - Clean text only
    a("┌" + "─" * (W-2) + "┐")
    a("│" + _center(gym_name) + "│")
    a("│" + _center("FITNESS CENTER") + "│")
    if gym_addr:
        for wl in _wrap(gym_addr):
            a("│" + _center(wl) + "│")
    if gym_phone:
        a("│" + _center(gym_phone) + "│")
    a("├" + "─" * (W-2) + "┤")
    a("│" + _center(copy_label) + "│")
    a("├" + "─" * (W-2) + "┤")
    a("│" + _left_right("RCPT:", receipt_no) + "│")
    a("│" + _left_right("DATE:", pay_date) + "│")
    a("│" + _left_right("TIME:", pay_time) + "│")
    a("│" + _left_right("BY:", collected) + "│")
    a("├" + "─" * (W-2) + "┤")
    a("│" + _center("MEMBER DETAILS") + "│")
    a("│" + _left_right("  ", "") + "│")
    for wl in _wrap(member_name):
        a("│" + "  " + wl.ljust(W-4) + "│")
    a("│" + _left_right("ID:", serial) + "│")
    a("│" + _left_right("TEL:", phone[:18]) + "│")
    a("├" + "─" * (W-2) + "┤")
    a("│" + _center("PAYMENT DETAILS") + "│")
    a("│" + _left_right("AMOUNT:", amount_str) + "│")
    a("│" + _left_right("METHOD:", method) + "│")
    a("│" + _left_right("STATUS:", "PAID") + "│")
    a("├" + "─" * (W-2) + "┤")
    a("│" + _left_right("FROM:", p_start) + "│")
    a("│" + _left_right("TO:", p_end) + "│")
    a("├" + "─" * (W-2) + "┤")
    a("│" + _center("Thank you for payment!") + "│")
    a("│" + _center("Keep this receipt") + "│")
    
    # Complaint / Support Number
    a("├" + "─" * (W-2) + "┤")
    a("│" + _center("Complaint / Support") + "│")
    a("│" + _center("WhatsApp: " + WHATSAPP_NUMBER) + "│")
    
    a("└" + "─" * (W-2) + "┘")
    a("")
    return "\n".join(lines)


def format_dual_receipts(data: dict) -> tuple:
    return (
        format_receipt(data, copy_label="MEMBER COPY"),
        format_receipt(data, copy_label="GYM COPY"),
    )


# ── On-screen Preview ──────────────────────────────────────────────────────────

def render_print_preview(data: dict, copies: int = 2):
    try:
        import streamlit as st
        st.markdown("### Print Preview (80mm Thermal)")
        
        if copies == 2:
            member_text, gym_text = format_dual_receipts(data)
            col1, col2 = st.columns(2)
            with col1:
                st.caption("Member Copy")
                st.markdown(f"""
                <div style="background:#1E1E2E;padding:15px;border-radius:10px;
                            border:2px solid #7C3AED;font-family:monospace;
                            font-size:13px;color:#E2E8F0;white-space:pre-wrap;
                            max-height:500px;overflow-y:auto;">
                    <pre style="color:#E2E8F0;font-family:monospace;font-size:13px;
                               margin:0;white-space:pre;font-weight:600;">{member_text}</pre>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.caption("Gym Copy")
                st.markdown(f"""
                <div style="background:#1E1E2E;padding:15px;border-radius:10px;
                            border:2px solid #7C3AED;font-family:monospace;
                            font-size:13px;color:#E2E8F0;white-space:pre-wrap;
                            max-height:500px;overflow-y:auto;">
                    <pre style="color:#E2E8F0;font-family:monospace;font-size:13px;
                               margin:0;white-space:pre;font-weight:600;">{gym_text}</pre>
                </div>
                """, unsafe_allow_html=True)
        else:
            text = format_receipt(data, "MEMBER COPY")
            st.markdown(f"""
            <div style="background:#1E1E2E;padding:15px;border-radius:10px;
                        border:2px solid #7C3AED;font-family:monospace;
                        font-size:13px;color:#E2E8F0;white-space:pre-wrap;
                        max-height:500px;overflow-y:auto;">
                <pre style="color:#E2E8F0;font-family:monospace;font-size:13px;
                           margin:0;white-space:pre;font-weight:600;">{text}</pre>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass


# ── Browser Print Component ────────────────────────────────────────────────────

def _build_receipt_html_body(data: dict, copies: int) -> str:
    """Build the <body> receipt blocks (escaped for HTML <pre>)."""
    import html as html_lib
    if copies == 2:
        member_text, gym_text = format_dual_receipts(data)
        return (
            f'<div class="receipt page-cut"><pre>{html_lib.escape(member_text)}</pre></div>'
            f'<div class="receipt"><pre>{html_lib.escape(gym_text)}</pre></div>'
        )
    else:
        text = format_receipt(data, "MEMBER COPY")
        return f'<div class="receipt"><pre>{html_lib.escape(text)}</pre></div>'


def render_print_component(data: dict, copies: int = 2):
    """
    Embed a printable receipt directly in the Streamlit page as an iframe.
    Contains a Print button + auto-triggers window.print() on load.
    """
    try:
        import streamlit as st

        body_html = _build_receipt_html_body(data, copies)
        receipt_no = data.get("receipt_no", "")
        line_count = body_html.count("\n") + (copies * 30)
        height = min(max(line_count * 14 + 200, 500), 900)

        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Receipt {receipt_no}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
    background: #1A1A2E;
    color: #E2E8F0;
    padding: 10px;
  }}
  .receipt {{
    background: #0F0F1A;
    width: 100%;
    max-width: 340px;
    margin: 0 auto 15px auto;
    padding: 12px;
    border: 2px solid #7C3AED;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(124,58,237,0.2);
  }}
  pre {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
    white-space: pre;
    line-height: 1.6;
    color: #E2E8F0;
    font-weight: 600;
  }}
  .btn-bar {{
    text-align: center;
    margin: 20px 0 10px 0;
  }}
  .print-btn {{
    padding: 16px 40px;
    background: #7C3AED;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    letter-spacing: 1px;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4);
  }}
  .print-btn:hover {{
    background: #6D28D9;
    transform: scale(1.02);
  }}
  .print-btn:active {{ background: #5B21B6; }}
  .hint {{
    text-align: center;
    font-size: 12px;
    color: #94A3B8;
    margin-top: 8px;
    font-weight: 500;
  }}
  
  @page {{ size: 80mm auto; margin: 2mm; }}
  
  @media print {{
    body {{
      background: #FFFFFF !important;
      padding: 0 !important;
    }}
    .btn-bar, .hint {{ display: none !important; }}
    .receipt {{
      background: #FFFFFF !important;
      border: 1px solid #000000 !important;
      max-width: 100% !important;
      box-shadow: none !important;
      padding: 8px !important;
      margin: 0 auto 10px auto !important;
    }}
    pre {{
      color: #000000 !important;
      font-weight: 700 !important;
      font-size: 11px !important;
      background: #FFFFFF !important;
    }}
    .page-cut {{
      page-break-after: always;
      break-after: page;
    }}
  }}
</style>
</head>
<body>
{body_html}
<div class="btn-bar">
  <button class="print-btn" onclick="window.print()">PRINT</button>
</div>
<p class="hint">Select your thermal printer in the print dialog</p>
<script>
  window.addEventListener('load', function() {{
    setTimeout(function() {{ window.print(); }}, 800);
  }});
</script>
</body>
</html>"""

        st.components.v1.html(full_html, height=height, scrolling=True)

    except Exception as e:
        try:
            import streamlit as st
            st.error(f"Could not render print component: {e}")
        except Exception:
            pass