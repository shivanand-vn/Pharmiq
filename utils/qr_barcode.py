"""
QR Code and Barcode generation utilities for invoices.
Uses ReportLab's built-in barcode support.
"""

import os
import tempfile

try:
    from reportlab.graphics.barcode import code128
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics import renderPM
    from reportlab.graphics.shapes import Drawing
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_qr_code(data, size=120, output_path=None):
    """
    Generate a QR code image for the given data string.
    Returns the output file path.
    """
    if not HAS_REPORTLAB:
        return None

    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "pharmiq_qr.png")

    qr = QrCodeWidget(data)
    bounds = qr.getBounds()
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
    drawing.add(qr)
    renderPM.drawToFile(drawing, output_path, fmt="PNG")
    return output_path


def generate_barcode_image(invoice_no, output_path=None):
    """
    Generate a Code128 barcode image for the invoice number.
    Returns the output file path.
    """
    if not HAS_REPORTLAB:
        return None

    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "pharmiq_barcode.png")

    barcode = code128.Code128(invoice_no, barWidth=1.2, barHeight=30)
    w, h = barcode.width, barcode.height
    drawing = Drawing(w, h)
    drawing.add(barcode)
    renderPM.drawToFile(drawing, output_path, fmt="PNG")
    return output_path
