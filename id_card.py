"""
Member ID Card Generator
PNG + PDF downloadable cards
"""
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from qr_utils import member_qr_png
import object_store


# Card dimensions (credit card size at 150 dpi)
CARD_W, CARD_H = 1012, 638   # ~85.6mm x 53.98mm at 300dpi (standard CR80)
BG_COLOR   = (15, 23, 42)    # Dark navy
ACCENT     = (99, 102, 241)  # Indigo
TEXT_COLOR = (248, 250, 252) # Near-white
MUTED      = (148, 163, 184) # Slate-400
WHITE      = (255, 255, 255)


def _load_font(size: int, bold: bool = False):
    """Load system font with fallback."""
    try:
        paths = (
            ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
            if bold else
            ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
        )
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    except Exception:
        pass
    return ImageFont.load_default()


def _draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*radius, y0 + 2*radius], fill=fill)
    draw.ellipse([x1 - 2*radius, y0, x1, y0 + 2*radius], fill=fill)
    draw.ellipse([x0, y1 - 2*radius, x0 + 2*radius, y1], fill=fill)
    draw.ellipse([x1 - 2*radius, y1 - 2*radius, x1, y1], fill=fill)


def generate_id_card_png(member, gym_name: str = "") -> bytes:
    """
    Member ID card PNG generate karo.
    Returns raw PNG bytes.
    """
    img = Image.new("RGB", (CARD_W, CARD_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Left accent bar
    draw.rectangle([0, 0, 12, CARD_H], fill=ACCENT)

    # Top gradient strip (solid accent band)
    draw.rectangle([12, 0, CARD_W, 90], fill=(30, 41, 59))

    # Gym name top-left
    gym_font   = _load_font(38, bold=True)
    title_font = _load_font(22)
    name_font  = _load_font(44, bold=True)
    label_font = _load_font(22)
    value_font = _load_font(26, bold=True)
    serial_font = _load_font(30, bold=True)

    gname = (gym_name or "GymPro").upper()
    draw.text((36, 22), gname, font=gym_font, fill=ACCENT)
    draw.text((36, 64), "MEMBERSHIP CARD", font=title_font, fill=MUTED)

    # ── Member photo (left side) ──────────────────────────────
    PHOTO_X, PHOTO_Y = 36, 110
    PHOTO_SIZE = 240

    b64, _ = object_store.get_photo_b64(member.photo_path or "")
    if b64:
        try:
            raw = base64.b64decode(b64)
            ph = Image.open(io.BytesIO(raw)).convert("RGB")
            ph = ph.resize((PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS)
            # Circular mask
            mask = Image.new("L", (PHOTO_SIZE, PHOTO_SIZE), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([0, 0, PHOTO_SIZE, PHOTO_SIZE], fill=255)
            ph.putalpha(mask)
            img.paste(ph, (PHOTO_X, PHOTO_Y), ph)
        except Exception:
            b64 = None

    if not b64:
        # Placeholder circle
        draw.ellipse([PHOTO_X, PHOTO_Y, PHOTO_X+PHOTO_SIZE, PHOTO_Y+PHOTO_SIZE],
                     fill=(30, 41, 59), outline=ACCENT, width=3)
        draw.text((PHOTO_X + PHOTO_SIZE//2 - 20, PHOTO_Y + PHOTO_SIZE//2 - 25),
                  "👤", font=_load_font(50), fill=MUTED)

    # Serial badge below photo
    serial = member.serial_number or "N/A"
    _draw_rounded_rect(draw, [PHOTO_X, PHOTO_Y+PHOTO_SIZE+12,
                               PHOTO_X+PHOTO_SIZE, PHOTO_Y+PHOTO_SIZE+52], 10, ACCENT)
    sw = draw.textlength(serial, font=serial_font)
    draw.text((PHOTO_X + (PHOTO_SIZE - sw)//2, PHOTO_Y+PHOTO_SIZE+16),
              serial, font=serial_font, fill=WHITE)

    # ── Member info (center) ──────────────────────────────────
    INFO_X = PHOTO_X + PHOTO_SIZE + 40
    INFO_Y = 110

    full_name = (member.full_name or "Member").upper()
    # Truncate if too long
    while draw.textlength(full_name, font=name_font) > 430 and len(full_name) > 5:
        full_name = full_name[:-1]
    if full_name != (member.full_name or "").upper():
        full_name += "…"
    draw.text((INFO_X, INFO_Y), full_name, font=name_font, fill=TEXT_COLOR)

    # Divider line
    draw.rectangle([INFO_X, INFO_Y+60, INFO_X+430, INFO_Y+62], fill=ACCENT)

    fields = [
        ("Membership", member.membership_type or "Standard"),
        ("Join Date",  str(member.join_date)[:10] if member.join_date else "N/A"),
        ("Valid Until", str(member.expiry_date)[:10] if member.expiry_date else "N/A"),
        ("Status",     (member.status or "Active").upper()),
        ("Phone",      member.phone or "—"),
    ]

    fy = INFO_Y + 76
    for label, value in fields:
        draw.text((INFO_X, fy), label + ":", font=label_font, fill=MUTED)
        draw.text((INFO_X + 170, fy), value, font=value_font, fill=TEXT_COLOR)
        fy += 42

    # ── QR code (right side) ─────────────────────────────────
    QR_SIZE = 200
    QR_X = CARD_W - QR_SIZE - 36
    QR_Y = 110

    qr_bytes = member_qr_png(serial, box_size=6, border=2)
    qr_img = Image.open(io.BytesIO(qr_bytes)).convert("RGB").resize(
        (QR_SIZE, QR_SIZE), Image.LANCZOS
    )
    img.paste(qr_img, (QR_X, QR_Y))

    draw.text((QR_X, QR_Y + QR_SIZE + 8), "SCAN FOR CHECK-IN",
              font=_load_font(18), fill=MUTED)

    # ── Footer bar ────────────────────────────────────────────
    draw.rectangle([0, CARD_H-50, CARD_W, CARD_H], fill=(30, 41, 59))
    draw.text((36, CARD_H-36), "Powered by GymPro",
              font=_load_font(20), fill=MUTED)
    draw.text((CARD_W-220, CARD_H-36), "Not Transferable",
              font=_load_font(20), fill=MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300))
    return buf.getvalue()


def generate_id_card_pdf(member, gym_name: str = "") -> bytes:
    """
    Member ID card PDF generate karo (A4, card center mein).
    Returns raw PDF bytes.
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader

    # Generate PNG first, then embed in PDF
    png_bytes = generate_id_card_png(member, gym_name)

    buf = io.BytesIO()
    page_w, page_h = A4
    c = rl_canvas.Canvas(buf, pagesize=A4)

    # Center the card on A4
    img_reader = ImageReader(io.BytesIO(png_bytes))
    card_pdf_w = page_w - 80   # 40pt margin each side
    card_pdf_h = card_pdf_w * (CARD_H / CARD_W)
    x = (page_w - card_pdf_w) / 2
    y = (page_h - card_pdf_h) / 2

    c.drawImage(img_reader, x, y, width=card_pdf_w, height=card_pdf_h,
                preserveAspectRatio=True)

    # Cut marks (dashed lines at card corners)
    c.setDash(3, 3)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    margin = 8
    c.rect(x - margin, y - margin, card_pdf_w + 2*margin, card_pdf_h + 2*margin)

    c.save()
    return buf.getvalue()
