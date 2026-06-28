"""
printer_utils.py
================
Universal 80mm thermal printer utility.
- 32-character line limit
- Plain text only (no emojis, no box-drawing chars)
- try-except everywhere so app never crashes on printer failure
- Works on Linux via 'lp' command
"""

import os
import subprocess
import tempfile
from datetime import datetime

W = 32  # 80mm thermal = 32 usable chars at standard font


# ── Formatting Helpers ─────────────────────────────────────────────────────────

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
    """Wrap long text into multiple lines."""
    words = str(text).split()
    lines = []
    current = ""
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


# ── Receipt Formatter ──────────────────────────────────────────────────────────

def format_receipt(data: dict, copy_label: str = "MEMBER COPY") -> str:
    """
    Build a 32-char-wide plain-text receipt string.

    Required keys in data:
        gym_name, receipt_no, date, time, collected_by,
        member_name, serial, phone, amount, method,
        period_start, period_end
    Optional:
        gym_address, gym_phone
    """
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
    a("")  # trailing newline for paper feed

    return "\n".join(lines)


def format_dual_receipts(data: dict) -> tuple:
    """Return (member_copy_text, gym_copy_text)."""
    member = format_receipt(data, copy_label="MEMBER COPY")
    gym    = format_receipt(data, copy_label="GYM COPY")
    return member, gym


# ── Printer Detection ──────────────────────────────────────────────────────────

def get_printer_name() -> str | None:
    """
    Return the first available thermal/POS printer name found via 'lpstat'.
    Returns None if nothing found or command fails.
    """
    try:
        result = subprocess.run(
            ["lpstat", "-a"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            lo = line.lower()
            if any(k in lo for k in ("thermal", "pos", "80mm", "bc-", "receipt")):
                return line.split()[0]
        # fallback: first printer
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        if lines:
            return lines[0].split()[0]
    except Exception:
        pass
    return None


def check_printer() -> tuple[bool, str]:
    """
    Returns (is_available: bool, message: str).
    Never raises an exception.
    """
    try:
        name = get_printer_name()
        if name:
            return True, f"Printer ready: {name}"
        return False, "No printer detected. Install CUPS or connect printer."
    except Exception as e:
        return False, f"Printer check failed: {e}"


# ── Print to Thermal ───────────────────────────────────────────────────────────

def print_thermal(text: str, printer_name: str = None) -> tuple[bool, str]:
    """
    Send plain-text receipt to thermal printer via 'lp'.
    Returns (success: bool, message: str).
    Never crashes the app.
    """
    try:
        if not printer_name:
            printer_name = get_printer_name()
        if not printer_name:
            return False, "No printer found. Check CUPS installation."

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            tmp_path = f.name

        try:
            cmd = ["lp", "-d", printer_name, tmp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return True, "Printed successfully."
            else:
                return False, f"lp error: {result.stderr.strip() or 'Unknown error'}"
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    except FileNotFoundError:
        return False, "Print command 'lp' not found. Install CUPS."
    except subprocess.TimeoutExpired:
        return False, "Printer timed out. Check connection."
    except Exception as e:
        return False, f"Print failed: {e}"


def print_single(data: dict, printer_name: str = None) -> tuple[bool, str]:
    """Print one member copy."""
    text = format_receipt(data, copy_label="MEMBER COPY")
    return print_thermal(text, printer_name)


def print_dual(data: dict, printer_name: str = None) -> tuple[bool, str]:
    """Print member copy then gym copy back-to-back."""
    member_text, gym_text = format_dual_receipts(data)
    combined = member_text + "\n" + _line("*") + "\n" + gym_text
    return print_thermal(combined, printer_name)


# ── Streamlit Preview ──────────────────────────────────────────────────────────

def render_print_preview(data: dict, copies: int = 2):
    """
    Show an on-screen preview of the receipt using st.code().
    Import streamlit here lazily so this module is importable without streamlit.
    """
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
            text = format_receipt(data, copy_label="MEMBER COPY")
            st.code(text, language=None)
    except Exception as e:
        pass
