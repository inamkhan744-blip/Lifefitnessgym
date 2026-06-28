"""
printer_utils.py
================
Browser-based 80mm thermal receipt printing for Streamlit.
No CUPS, no system commands — works on any device (mobile, desktop).
"""

from datetime import datetime

W = 32  # 80mm thermal = 32 usable chars at standard font


# ── Text Formatting Helpers ────────────────────────────────────────────────────

def _line(char="-"):
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
    a(_line("="))
    a(_center(gym_name))
    a(_center("FITNESS CENTER"))
    if gym_addr:
        for wl in _wrap(gym_addr):
            a(_center(wl))
    if gym_phone:
        a(_center(gym_phone))
    a(_line("="))
    a(_center(copy_label))
    a(_line("-"))
    a(_left_right("RCPT:", receipt_no))
    a(_left_right("DATE:", pay_date))
    a(_left_right("TIME:", pay_time))
    a(_left_right("BY:  ", collected))
    a(_line("-"))
    a("MEMBER:")
    for wl in _wrap(member_name):
        a("  " + wl)
    a(_left_right("ID:  ", serial))
    a(_left_right("TEL: ", phone[:18]))
    a(_line("-"))
    a(_left_right("AMOUNT:", amount_str))
    a(_left_right("METHOD:", method))
    a(_left_right("STATUS:", "PAID"))
    a(_line("-"))
    a(_left_right("FROM:", p_start))
    a(_left_right("TO:  ", p_end))
    a(_line("="))
    a(_center("Thank you for payment!"))
    a(_center("Keep this receipt."))
    a(_line("="))
    a("")
    return "\n".join(lines)


def format_dual_receipts(data: dict) -> tuple:
    return (
        format_receipt(data, copy_label="MEMBER COPY"),
        format_receipt(data, copy_label="GYM COPY"),
    )


# ── On-screen Preview (uses st.code) ──────────────────────────────────────────

def render_print_preview(data: dict, copies: int = 2):
    try:
        import streamlit as st
        st.markdown("**Print Preview (80mm Thermal)**")
        if copies == 2:
            member_text, gym_text = format_dual_receipts(data)
            col1, col2 = st.columns(2)
            with col1:
                st.caption("Member Copy")
                st.code(member_text, language=None)
            with col2:
                st.caption("Gym Copy")
                st.code(gym_text, language=None)
        else:
            st.code(format_receipt(data, "MEMBER COPY"), language=None)
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
    Works on mobile Chrome, desktop Chrome, Safari, Firefox.
    No popups, no data-URIs, no CUPS.
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
    font-size: 12px;
    background: #f5f5f5;
    color: #000;
    padding: 10px;
  }}
  .receipt {{
    background: #fff;
    width: 100%;
    max-width: 320px;
    margin: 0 auto 12px auto;
    padding: 8px;
    border: 1px dashed #999;
    border-radius: 4px;
  }}
  pre {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 11px;
    white-space: pre;
    line-height: 1.45;
    color: #000;
  }}
  .cut {{
    text-align: center;
    color: #999;
    font-size: 10px;
    margin: 4px 0;
    letter-spacing: 4px;
  }}
  .cut::before {{ content: "- - - - - - - - - - - - - - - -"; }}
  .btn-bar {{
    text-align: center;
    margin: 16px 0 8px 0;
  }}
  .print-btn {{
    padding: 14px 36px;
    background: #7C3AED;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    letter-spacing: 1px;
  }}
  .print-btn:active {{ background: #6D28D9; }}
  .hint {{
    text-align: center;
    font-size: 11px;
    color: #666;
    margin-top: 6px;
  }}
  @page {{ size: 80mm auto; margin: 2mm; }}
  @media print {{
    body {{ background:#fff; padding:0; }}
    .btn-bar, .hint {{ display: none !important; }}
    .receipt {{ border: none; max-width: 100%; }}
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
  <button class="print-btn" onclick="window.print()">🖨️ PRINT</button>
</div>
<p class="hint">Select your thermal printer in the print dialog</p>
<script>
  window.addEventListener('load', function() {{
    setTimeout(function() {{ window.print(); }}, 600);
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
