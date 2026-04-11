"""
PDF Invoice Generator using ReportLab.
Generates a professional A4 pharma tax invoice matching the reference layout.
"""

import os
import tempfile
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
)
from reportlab.pdfgen import canvas

from services.invoice_service import build_gst_summary


# ── Colours ──────────────────────────────────────────
DARK = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#16213e")
BORDER = colors.HexColor("#333333")
LIGHT_BG = colors.HexColor("#f5f5f5")
WHITE = colors.white
HEADER_BG = colors.HexColor("#e8e8e8")


def _styles():
    """Return custom paragraph styles."""
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "InvTitle", parent=ss["Title"],
            fontSize=16, leading=20, alignment=TA_CENTER,
            fontName="Helvetica-Bold", textColor=DARK,
        ),
        "subtitle": ParagraphStyle(
            "InvSubtitle", parent=ss["Normal"],
            fontSize=10, leading=13, alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "normal": ParagraphStyle(
            "InvNormal", parent=ss["Normal"],
            fontSize=8, leading=10, fontName="Helvetica",
        ),
        "normal_bold": ParagraphStyle(
            "InvNormalBold", parent=ss["Normal"],
            fontSize=8, leading=10, fontName="Helvetica-Bold",
        ),
        "small": ParagraphStyle(
            "InvSmall", parent=ss["Normal"],
            fontSize=7, leading=9, fontName="Helvetica",
        ),
        "small_bold": ParagraphStyle(
            "InvSmallBold", parent=ss["Normal"],
            fontSize=7, leading=9, fontName="Helvetica-Bold",
        ),
        "right": ParagraphStyle(
            "InvRight", parent=ss["Normal"],
            fontSize=8, leading=10, fontName="Helvetica", alignment=TA_RIGHT,
        ),
        "right_bold": ParagraphStyle(
            "InvRightBold", parent=ss["Normal"],
            fontSize=8, leading=10, fontName="Helvetica-Bold", alignment=TA_RIGHT,
        ),
        "amount_words": ParagraphStyle(
            "InvAmtWords", parent=ss["Normal"],
            fontSize=8, leading=10, fontName="Helvetica-BoldOblique",
        ),
        "footer_small": ParagraphStyle(
            "FooterSmall", parent=ss["Normal"],
            fontSize=6.5, leading=8, fontName="Helvetica",
        ),
    }


def generate_invoice_pdf(invoice, distributor, customer, output_path=None):
    """
    Generate a professional A4 PDF invoice.

    Parameters:
        invoice: dict from get_invoice() (includes 'items' list)
        distributor: dict from get_distributor_by_id()
        customer: dict from get_customer_by_license()
        output_path: optional output file path

    Returns: absolute path to the generated PDF file.
    """
    if output_path is None:
        output_dir = r"F:\Pharmiq\Invoice"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            f"{invoice['invoice_no']}.pdf"
        )

    st = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm,
    )

    elements = []
    page_width = A4[0] - 24 * mm  # usable width

    # ══════════════════════════════════════════════════
    # HEADER: Company info (left) | TAX INVOICE (center) | Party info (right)
    # ══════════════════════════════════════════════════

    # --- Company column (left) ---
    company_lines = []
    company_lines.append(Paragraph(f"<b>{distributor.get('name', '')}</b>", st["normal_bold"]))
    if distributor.get("address"):
        company_lines.append(Paragraph(distributor["address"], st["small"]))
    phone_line = ""
    if distributor.get("mobile_no"):
        phone_line += f"Phone: {distributor['mobile_no']}"
    if distributor.get("email"):
        phone_line += f"  |  {distributor['email']}"
    if phone_line:
        company_lines.append(Paragraph(phone_line, st["small"]))
    if distributor.get("gst_no"):
        company_lines.append(Paragraph(f"GSTIN: {distributor['gst_no']}", st["small"]))
    if distributor.get("drug_license_no"):
        company_lines.append(Paragraph(f"D.L. No: {distributor['drug_license_no']}", st["small"]))

    company_cell = company_lines

    # --- Logo (if available) ---
    logo_cell = []
    logo_path = distributor.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        try:
            logo_cell.append(Image(logo_path, width=40, height=40))
        except Exception:
            pass

    # --- Center column ---
    center_cell = [
        Paragraph("<b>TAX INVOICE</b>", st["title"]),
        Paragraph(f"<b>{invoice.get('payment_type', 'Credit').upper()}</b>", st["subtitle"]),
    ]

    # --- Party / Customer column (right) ---
    party_lines = []
    party_lines.append(Paragraph("<b>Party Name:</b>", st["small_bold"]))
    party_lines.append(Paragraph(f"<b>{customer.get('license_holder_name', '')}</b>", st["normal_bold"]))
    if customer.get("shop_name"):
        party_lines.append(Paragraph(customer["shop_name"], st["small"]))
    if customer.get("address"):
        party_lines.append(Paragraph(customer["address"], st["small"]))
    if customer.get("mobile_no"):
        party_lines.append(Paragraph(f"PHONE: {customer['mobile_no']}", st["small"]))
    if customer.get("gst_no"):
        party_lines.append(Paragraph(f"GSTIN: {customer['gst_no']}", st["small"]))
    if customer.get("license_no"):
        party_lines.append(Paragraph(f"Licence No: {customer['license_no']}", st["small"]))

    party_cell = party_lines

    header_data = [[
        logo_cell + company_cell,
        center_cell,
        party_cell,
    ]]

    header_table = Table(header_data, colWidths=[page_width * 0.35, page_width * 0.25, page_width * 0.40])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_table)

    # ══════════════════════════════════════════════════
    # INVOICE META: Invoice No, Date, Order No, LR No, Transport
    # ══════════════════════════════════════════════════
    inv_date = invoice.get("invoice_date", "")
    if hasattr(inv_date, "strftime"):
        inv_date = inv_date.strftime("%d/%m/%Y")

    meta_data = [[
        Paragraph(f"<b>Invoice No:</b> {invoice.get('invoice_no', '')}", st["small"]),
        Paragraph("", st["small"]),
        Paragraph(f"<b>Cases:</b> 0", st["small"]),
    ], [
        Paragraph(f"<b>Invoice Date:</b> {inv_date}", st["small"]),
        Paragraph(f"<b>Near Date:</b> ", st["small"]),
        Paragraph("", st["small"]),
    ], [
        Paragraph(f"<b>Due Date:</b> ", st["small"]),
        Paragraph("", st["small"]),
        Paragraph(f"<b>Licence No:</b> {customer.get('license_no', '')}", st["small"]),
    ]]

    meta_table = Table(meta_data, colWidths=[page_width * 0.34, page_width * 0.33, page_width * 0.33])
    meta_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)

    # ══════════════════════════════════════════════════
    # PRODUCT TABLE
    # ══════════════════════════════════════════════════
    col_widths = [
        page_width * 0.04,   # Sl No
        page_width * 0.06,   # Mfg
        page_width * 0.18,   # Product Name
        page_width * 0.06,   # Packs
        page_width * 0.10,   # Batch
        page_width * 0.07,   # Exp
        page_width * 0.07,   # MRP
        page_width * 0.06,   # Tot Qty
        page_width * 0.07,   # Rate
        page_width * 0.06,   # Dis%
        page_width * 0.07,   # Free Dis Val
        page_width * 0.08,   # Value*
        page_width * 0.04,   # *GST
        page_width * 0.04,   # HSN
    ]

    # Header row
    headers = [
        Paragraph("<b>Sl No</b>", st["small_bold"]),
        Paragraph("<b>Mfg</b>", st["small_bold"]),
        Paragraph("<b>Product Name</b>", st["small_bold"]),
        Paragraph("<b>Packs</b>", st["small_bold"]),
        Paragraph("<b>Batch</b>", st["small_bold"]),
        Paragraph("<b>Exp</b>", st["small_bold"]),
        Paragraph("<b>M.R.P</b>", st["small_bold"]),
        Paragraph("<b>Tot Qty</b>", st["small_bold"]),
        Paragraph("<b>TRP</b>", st["small_bold"]),
        Paragraph("<b>Dis%</b>", st["small_bold"]),
        Paragraph("<b>Free Dis Val*</b>", st["small_bold"]),
        Paragraph("<b>Value*</b>", st["small_bold"]),
        Paragraph("<b>*GST</b>", st["small_bold"]),
        Paragraph("<b>HSN</b>", st["small_bold"]),
    ]

    product_rows = [headers]

    items = invoice.get("items", [])
    for idx, item in enumerate(items, 1):
        exp_date = item.get("expiry_date", "")
        if hasattr(exp_date, "strftime"):
            exp_date = exp_date.strftime("%m/%y")

        row = [
            Paragraph(str(idx), st["small"]),
            Paragraph("", st["small"]),  # Mfg
            Paragraph(str(item.get("product_name", "")), st["small"]),
            Paragraph(str(item.get("qty", "")), st["small"]),
            Paragraph(str(item.get("batch_no", "")), st["small"]),
            Paragraph(str(exp_date), st["small"]),
            Paragraph(f"{float(item.get('mrp', 0)):.2f}", st["small"]),
            Paragraph(str(item.get("qty", "")), st["small"]),
            Paragraph(f"{float(item.get('trp', 0)):.2f}", st["small"]),
            Paragraph(f"{float(item.get('discount_percent', 0)):.1f}", st["small"]),
            Paragraph("", st["small"]),
            Paragraph(f"{float(item.get('amount', 0)):.2f}", st["small"]),
            Paragraph(f"{float(item.get('gst_percent', 0)):.0f}", st["small"]),
            Paragraph("", st["small"]),  # HSN
        ]
        product_rows.append(row)

    # Add empty rows to fill space (minimum 10 rows for clean look)
    while len(product_rows) < 10:
        product_rows.append([""] * 14)

    product_table = Table(product_rows, colWidths=col_widths, repeatRows=1)
    product_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        # Data
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        # Borders
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Alternate rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]))
    elements.append(product_table)

    # ══════════════════════════════════════════════════
    # GST SUMMARY + TOTALS SECTION
    # ══════════════════════════════════════════════════
    gst_summary = build_gst_summary(items)

    # GST breakdown table (left side)
    gst_headers = [
        Paragraph("<b>CLASS</b>", st["small_bold"]),
        Paragraph("<b>TOTAL</b>", st["small_bold"]),
        Paragraph("<b>SCHEME</b>", st["small_bold"]),
        Paragraph("<b>DISCOUNT</b>", st["small_bold"]),
        Paragraph("<b>SGST</b>", st["small_bold"]),
        Paragraph("<b>CGST</b>", st["small_bold"]),
        Paragraph("<b>TOTAL GST</b>", st["small_bold"]),
    ]
    gst_rows = [gst_headers]
    total_taxable = 0
    total_sgst_sum = 0
    total_cgst_sum = 0
    total_gst_sum = 0

    for gs in gst_summary:
        gst_rows.append([
            Paragraph(f"GST {gs['gst_percent']:.2f}%", st["small"]),
            Paragraph(f"{gs['taxable_amount']:.2f}", st["small"]),
            Paragraph("0.00", st["small"]),
            Paragraph(f"{invoice.get('discount_amount', 0):.2f}" if gs == gst_summary[0] else "0.00", st["small"]),
            Paragraph(f"{gs['sgst']:.2f}", st["small"]),
            Paragraph(f"{gs['cgst']:.2f}", st["small"]),
            Paragraph(f"{gs['total_gst']:.2f}", st["small"]),
        ])
        total_taxable += gs["taxable_amount"]
        total_sgst_sum += gs["sgst"]
        total_cgst_sum += gs["cgst"]
        total_gst_sum += gs["total_gst"]

    # Total row
    gst_rows.append([
        Paragraph("<b>TOTAL</b>", st["small_bold"]),
        Paragraph(f"<b>{total_taxable:.2f}</b>", st["small_bold"]),
        Paragraph("<b>0.00</b>", st["small_bold"]),
        Paragraph(f"<b>{invoice.get('discount_amount', 0):.2f}</b>", st["small_bold"]),
        Paragraph(f"<b>{total_sgst_sum:.2f}</b>", st["small_bold"]),
        Paragraph(f"<b>{total_cgst_sum:.2f}</b>", st["small_bold"]),
        Paragraph(f"<b>{total_gst_sum:.2f}</b>", st["small_bold"]),
    ])

    gst_col_widths = [page_width * 0.10, page_width * 0.10, page_width * 0.09,
                      page_width * 0.10, page_width * 0.09, page_width * 0.09, page_width * 0.10]
    gst_table = Table(gst_rows, colWidths=gst_col_widths)
    gst_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("LINEABOVE", (0, -1), (-1, -1), 1, BORDER),
    ]))

    # Right side: Items count, totals
    total_items = len(items)
    total_qty = sum(int(it.get("qty", 0)) for it in items)

    totals_data = [
        [Paragraph(f"Total Items  :  {total_items}", st["small_bold"]),
         Paragraph("", st["small"]),
         Paragraph(f"<b>{total_taxable:.2f}</b>", st["right_bold"])],
        [Paragraph(f"Total Qty  :  {total_qty}", st["small_bold"]),
         Paragraph("", st["small"]),
         Paragraph("", st["right"])],
        [Paragraph("", st["small"]),
         Paragraph("DIS AMT", st["small"]),
         Paragraph(f"{invoice.get('discount_amount', 0):.2f}", st["right"])],
        [Paragraph("", st["small"]),
         Paragraph("SGST PAYBLE", st["small"]),
         Paragraph(f"{invoice.get('sgst', 0):.2f}", st["right"])],
        [Paragraph("", st["small"]),
         Paragraph("CGST PAYBLE", st["small"]),
         Paragraph(f"{invoice.get('cgst', 0):.2f}", st["right"])],
        [Paragraph("", st["small"]),
         Paragraph("ROUND NOTE:", st["small"]),
         Paragraph("0.00", st["right"])],
    ]

    totals_col = [page_width * 0.10, page_width * 0.12, page_width * 0.11]
    totals_table = Table(totals_data, colWidths=totals_col)
    totals_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    # Combine GST summary and totals side by side
    summary_row = [[gst_table, totals_table]]
    summary_table = Table(summary_row, colWidths=[page_width * 0.67, page_width * 0.33])
    summary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(summary_row_spacer := Spacer(1, 2))
    elements.append(summary_table)

    # ══════════════════════════════════════════════════
    # AMOUNT IN WORDS + GRAND TOTAL
    # ══════════════════════════════════════════════════
    amt_words = invoice.get("amount_in_words", "")
    grand_total = float(invoice.get("grand_total", 0))

    amt_gt_data = [[
        Paragraph(f"<b>{amt_words}</b>", st["amount_words"]),
        Paragraph("<b>Grand Total</b>", st["right_bold"]),
    ], [
        Paragraph("", st["small"]),
        Paragraph(f"<b>{grand_total:.2f}</b>",
                  ParagraphStyle("GT", parent=st["right_bold"], fontSize=14, leading=16)),
    ]]
    amt_gt_table = Table(amt_gt_data, colWidths=[page_width * 0.65, page_width * 0.35])
    amt_gt_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(amt_gt_table)

    # ══════════════════════════════════════════════════
    # FOOTER: User, Terms, Bank Details, Signatory
    # ══════════════════════════════════════════════════
    elements.append(Spacer(1, 3))

    # Bank details
    bank_line = "Bank Details: "
    if distributor.get("bank_name"):
        bank_line += f"A/C No {distributor.get('bank_account_no', '')}, "
        bank_line += f"IFSCODE {distributor.get('bank_ifsc', '')}  "
        bank_line += f"{distributor.get('bank_name', '')}, "
        bank_line += f"{distributor.get('bank_branch', '')}"
    if distributor.get("bank_upi"):
        bank_line += f"  PhonePE No.{distributor.get('mobile_no', '')}"

    signatory_content = [
        Paragraph(f"FOR  <b>{distributor.get('name', '')}</b>", st["small_bold"]),
        Spacer(1, 15),
        Paragraph("<b>Authorized Signatory</b>", st["small_bold"]),
    ]

    # Check for signatory image
    sig_path = distributor.get("signatory_img_path")
    if sig_path and os.path.exists(sig_path):
        try:
            signatory_content.insert(1, Image(sig_path, width=50, height=25))
        except Exception:
            pass

    footer_data = [[
        [
            Paragraph("<b><u>Terms & Conditions</u></b>", st["small_bold"]),
            Spacer(1, 4),
            Paragraph(bank_line, st["footer_small"]),
        ],
        signatory_content,
    ]]

    footer_table = Table(footer_data, colWidths=[page_width * 0.65, page_width * 0.35])
    footer_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (0, -1), "TOP"),
        ("VALIGN", (1, 0), (1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(footer_table)

    # ── Build PDF ──
    doc.build(elements)
    return output_path


def open_pdf(pdf_path):
    """Open PDF in default system viewer."""
    import subprocess
    import platform

    system = platform.system()
    if system == "Windows":
        os.startfile(pdf_path)
    elif system == "Darwin":
        subprocess.run(["open", pdf_path])
    else:
        subprocess.run(["xdg-open", pdf_path])


def print_pdf(pdf_path):
    """Send PDF to default printer (Windows)."""
    import subprocess
    import platform

    system = platform.system()
    if system == "Windows":
        os.startfile(pdf_path, "print")
    else:
        subprocess.run(["lpr", pdf_path])
