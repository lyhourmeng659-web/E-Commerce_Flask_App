"""
Invoice PDF Generator — ShopHub
Generates a professional PDF invoice using ReportLab (pure Python).

Design matches master.html UI:
  - Indigo (#4F46E5) primary accent, matching the web UI
  - Outfit-style bold headings via Helvetica-Bold
  - Slate color palette throughout
  - Clean two-column layout, rounded feel via spacing
  - Status badge with color-coded pill
  - Consistent card-like section separation

WHY ReportLab instead of WeasyPrint:
  WeasyPrint requires GTK/Pango system libraries that are NOT available
  on Windows without a full GTK runtime. ReportLab is pure Python:
      pip install reportlab

Usage:
    from app.modules.orders.pdf import generate_invoice_pdf
    pdf_bytes = generate_invoice_pdf(order)
"""

import io
from decimal import Decimal

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

#  Design tokens (mirrors master.html CSS variables)
INDIGO = HexColor("#4F46E5")
INDIGO_DARK = HexColor("#3730A3")
INDIGO_SOFT = HexColor("#EEF2FF")
INK = HexColor("#0F172A")
INK_MUTED = HexColor("#64748B")
INK_LIGHT = HexColor("#CBD5E1")
SURFACE = HexColor("#FFFFFF")
SURFACE_2 = HexColor("#F8FAFC")
BORDER = HexColor("#E2E8F0")
GREEN = HexColor("#059669")
GREEN_BG = HexColor("#ECFDF5")
RED = HexColor("#EF4444")
RED_BG = HexColor("#FEF2F2")
AMBER = HexColor("#D97706")
AMBER_BG = HexColor("#FFFBEB")

STATUS_COLORS = {
    "delivered": (GREEN, GREEN_BG),
    "shipped": (INDIGO, INDIGO_SOFT),
    "paid": (AMBER, AMBER_BG),
    "cancelled": (RED, RED_BG),
    "pending": (INK_MUTED, SURFACE_2),
    "refunded": (INK_MUTED, SURFACE_2),
}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
USABLE_W = PAGE_W - 2 * MARGIN


#  Style helpers

def _s(name, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, **kw)


def _p(text, style) -> Paragraph:
    return Paragraph(text, style)


#  Shared paragraph styles
EYEBROW = _s("Eyebrow",
             fontSize=7, fontName="Helvetica-Bold",
             textColor=INDIGO, leading=10, spaceAfter=4)

BODY_LG = _s("BodyLg",
             fontSize=11, fontName="Helvetica-Bold",
             textColor=INK, leading=15)

BODY_MUTED = _s("BodyMuted", fontSize=9.5, textColor=INK_MUTED, leading=13)

KEY = _s("Key", fontSize=9, fontName="Helvetica-Bold",
         textColor=INK_MUTED, leading=13)
VAL = _s("Val", fontSize=9, fontName="Helvetica-Bold",
         textColor=INK, leading=13, alignment=TA_RIGHT)

TH = _s("TH", fontSize=8, fontName="Helvetica-Bold",
        textColor=INK_MUTED, leading=10)
THC = _s("THC", fontSize=8, fontName="Helvetica-Bold",
         textColor=INK_MUTED, leading=10, alignment=TA_CENTER)
THR = _s("THR", fontSize=8, fontName="Helvetica-Bold",
         textColor=INK_MUTED, leading=10, alignment=TA_RIGHT)

TD = _s("TD", fontSize=10, textColor=INK, leading=14)
TDC = _s("TDC", fontSize=10, textColor=INK_MUTED, leading=14, alignment=TA_CENTER)
TDR = _s("TDR", fontSize=10, textColor=INK, leading=14,
         alignment=TA_RIGHT, fontName="Helvetica-Bold")

TOTAL_LBL = _s("TotalLbl", fontSize=10, textColor=INK_MUTED, leading=16)
TOTAL_VAL = _s("TotalVal", fontSize=10, textColor=INK, leading=16,
               alignment=TA_RIGHT, fontName="Helvetica-Bold")
GRAND_LBL = _s("GrandLbl", fontSize=11, textColor=INK, leading=16,
               fontName="Helvetica-Bold")

GRAND_VAL = _s("GrandVal", fontSize=16, textColor=INDIGO, leading=20,
               alignment=TA_RIGHT, fontName="Helvetica-Bold")

FOOTER_ST = _s("Footer", fontSize=8, textColor=INK_LIGHT,
               leading=12, alignment=TA_CENTER)


#  Public entry point

def generate_invoice_pdf(order) -> bytes:
    """Build and return a PDF invoice as raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Invoice #{order.order_number}",
        author="ShopHub.",
    )

    story = []
    _build_header(story, order)
    _build_meta_row(story, order)
    _build_address_block(story, order)
    _build_divider(story, thick=1.5, color=INK, space_before=2, space_after=5)
    _build_items_table(story, order)
    _build_divider(story, thick=0.5, color=BORDER, space_before=2, space_after=4)
    _build_totals(story, order)
    _build_footer(story)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    current_app.logger.info(
        f"[PDF] Invoice #{order.order_number} generated ({len(pdf_bytes):,} bytes)"
    )
    return pdf_bytes


#  Section builders

def _build_header(story, order):
    """
    Indigo banner: ShopHub brand (left) + order number & date (right).
    """
    order_num = getattr(order, "order_number", str(order.id))
    order_date = order.created_at.strftime("%d %b %Y")

    brand_p = _p(
        "<font color='#FFFFFF'><b>ShopHub.</b></font>",
        _s("BH", fontSize=18, fontName="Helvetica-Bold",
           textColor=white, leading=22),
    )

    tag_p = _p(
        "<font color='#C7D2FE'>INVOICE</font>",
        _s("TG", fontSize=8, fontName="Helvetica-Bold",
           textColor=HexColor("#C7D2FE"), leading=11),
    )

    num_p = _p(
        f"<font color='#FFFFFF'><b>#{order_num}</b></font>",
        _s("NH", fontSize=14, fontName="Helvetica-Bold",
           textColor=white, leading=16),
    )

    date_p = _p(
        f"<font color='#C7D2FE'>{order_date}</font>",
        _s("DH", fontSize=9, textColor=HexColor("#C7D2FE"),
           leading=13),
    )

    L = USABLE_W * 0.55
    R = USABLE_W * 0.45

    left_t = Table([[brand_p], [tag_p]], colWidths=[L])
    right_t = Table([[num_p], [date_p]], colWidths=[R])
    for t in (left_t, right_t):
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

    banner = Table([[left_t, right_t]], colWidths=[L, R])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INDIGO),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (0, -1), 20),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 20),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 7 * mm))


def _build_meta_row(story, order):
    """Status pill + Payment + Date summary row."""
    status = order.status.replace("_", " ").title()
    s_clr, s_bg = STATUS_COLORS.get(order.status, (INK_MUTED, SURFACE_2))
    payment = getattr(order, "payment_method", "—")
    order_date = order.created_at.strftime("%d %b %Y")

    status_p = _p(
        f"<b>{status}</b>",
        _s("SP", fontSize=8, fontName="Helvetica-Bold",
           textColor=s_clr, leading=11, alignment=TA_CENTER),
    )
    pay_p = _p(
        f"<font color='#94A3B8' size='8'>PAYMENT&nbsp;&nbsp;</font><b>{payment}</b>",
        _s("PP", fontSize=9, textColor=INK, leading=13),
    )
    date_p = _p(
        f"<font color='#94A3B8' size='8'>DATE&nbsp;&nbsp;</font><b>{order_date}</b>",
        _s("DP2", fontSize=9, textColor=INK, leading=13, alignment=TA_RIGHT),
    )

    pill = Table([[status_p]], colWidths=[USABLE_W * 0.22])
    pill.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), s_bg),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))

    meta = Table(
        [[pill, pay_p, date_p]],
        colWidths=[USABLE_W * 0.24, USABLE_W * 0.44, USABLE_W * 0.32],
    )
    meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(meta)
    story.append(Spacer(1, 6 * mm))


def _build_address_block(story, order):
    """Two-column: Ship To (left) | Order Details key-value (right)."""
    col_r = USABLE_W * 0.42 - 8

    ship = [
        _p("SHIP TO", EYEBROW),
        _p(f"<b>{order.customer_name}</b>", BODY_LG),
        Spacer(1, 2),
        _p(order.address, BODY_MUTED),
        _p(f"{order.city}, {order.zip_code}", BODY_MUTED),
        _p(order.country, BODY_MUTED),
        Spacer(1, 4),
        _p(order.customer_email, BODY_MUTED),
    ]

    details = [_p("ORDER DETAILS", EYEBROW)]
    for k, v in [
        ("Order #", getattr(order, "order_number", str(order.id))),
        ("Status", order.status.replace("_", " ").title()),
        ("Payment", getattr(order, "payment_method", "—")),
        ("Date", order.created_at.strftime("%d %b %Y")),
    ]:
        row = Table(
            [[_p(k, KEY), _p(v, VAL)]],
            colWidths=[col_r * 0.44, col_r * 0.56],
        )
        row.setStyle(TableStyle([
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ]))
        details.append(row)

    addr = Table([[ship, details]],
                 colWidths=[USABLE_W * 0.55, USABLE_W * 0.45])
    addr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, BORDER),
        ("LEFTPADDING", (1, 0), (1, -1), 14),
    ]))
    story.append(addr)
    story.append(Spacer(1, 6 * mm))


def _build_divider(story, thick=0.5, color=BORDER, space_before=2, space_after=4):
    story.append(Spacer(1, space_before * mm))
    story.append(HRFlowable(width="100%", thickness=thick, color=color,
                            spaceAfter=0, spaceBefore=0))
    story.append(Spacer(1, space_after * mm))


def _build_items_table(story, order):
    """Line-items table with alternating surface row backgrounds."""
    story.append(_p("ITEMS", EYEBROW))
    story.append(Spacer(1, 2 * mm))

    col_w = [USABLE_W * 0.50, USABLE_W * 0.12,
             USABLE_W * 0.19, USABLE_W * 0.19]

    rows = [[
        _p("PRODUCT", TH),
        _p("QTY", THC),
        _p("UNIT PRICE", THR),
        _p("TOTAL", THR),
    ]]
    for i, item in enumerate(order.items):
        unit = Decimal(str(item.price))
        total = unit * item.quantity
        rows.append([
            _p(item.product_name, TD),
            _p(str(item.quantity), TDC),
            _p(f"${unit:.2f}", TDR),
            _p(f"${total:.2f}", TDR),
        ])

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), SURFACE_2),
        ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]
    for r in range(1, len(rows)):
        bg = SURFACE if r % 2 == 1 else SURFACE_2
        style_cmds.append(("BACKGROUND", (0, r), (-1, r), bg))

    items_t = Table(rows, colWidths=col_w, repeatRows=1)
    items_t.setStyle(TableStyle(style_cmds))
    story.append(KeepTogether(items_t))
    story.append(Spacer(1, 4 * mm))


def _build_totals(story, order):
    """
    Right-aligned totals block.
    """
    right_w = USABLE_W * 0.42  # wider block
    left_sp = USABLE_W - right_w

    subtotal = Decimal(str(order.total_amount)) - Decimal(str(order.shipping_amount))
    shipping = Decimal(str(order.shipping_amount))
    ship_str = "FREE" if shipping == 0 else f"${shipping:.2f}"
    ship_color = GREEN if shipping == 0 else INK

    ship_val_style = _s("ShipV", fontSize=10, textColor=ship_color, leading=16,
                        alignment=TA_RIGHT, fontName="Helvetica-Bold")

    totals_data = [
        [_p("Subtotal", TOTAL_LBL), _p(f"${subtotal:.2f}", TOTAL_VAL)],
        [_p("Shipping", TOTAL_LBL), _p(ship_str, ship_val_style)],
        [_p("", TOTAL_LBL), _p("", TOTAL_VAL)],  # breathing row
        [_p("Total Paid", GRAND_LBL), _p(f"${order.total_amount:.2f}", GRAND_VAL)],
    ]

    totals_t = Table(totals_data,
                     colWidths=[right_w * 0.45, right_w * 0.55])
    totals_t.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, BORDER),  # above subtotal
        ("LINEABOVE", (0, 3), (-1, 3), 1.5, INK),  # above grand total
        ("TOPPADDING", (0, 3), (-1, 3), 10),
        ("BOTTOMPADDING", (0, 3), (-1, 3), 8),
        ("BACKGROUND", (0, 3), (-1, 3), INDIGO_SOFT),
        ("LEFTPADDING", (0, 3), (-1, 3), 10),
        ("RIGHTPADDING", (-1, 3), (-1, 3), 10),
    ]))

    wrapper = Table([[Spacer(left_sp, 1), totals_t]],
                    colWidths=[left_sp, right_w])
    wrapper.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(wrapper)
    story.append(Spacer(1, 10 * mm))


def _build_footer(story):
    """Thin rule + centred copyright line."""
    _build_divider(story, thick=0.5, color=BORDER, space_before=0, space_after=3)
    story.append(_p(
        "© 2026 ShopHub · Cambodia · Thank you for your order!",
        FOOTER_ST,
    ))
