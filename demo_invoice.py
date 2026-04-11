"""
Invoice Preview Demo — Generates a professional PDF invoice with dummy data.
No MySQL required. Run: python demo_invoice.py
"""

import os
import sys
import tempfile
from datetime import date, datetime

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.num_to_words import number_to_words
from services.invoice_service import calculate_item_amount, build_gst_summary


def generate_demo_pdf():
    """Generate a complete demo invoice PDF with dummy data."""

    # ── Dummy distributor ──
    distributor = {
        "distributor_id": 1,
        "name": "SV PHARMACEUTICALS",
        "mobile_no": "9876543210",
        "email": "svpharma@email.com",
        "address": "1st Floor, Trade Center, Station Road, Hubli - 580021, Karnataka",
        "gst_no": "29AABCS1234F1Z5",
        "drug_license_no": "KA-HB-20B1/21B1-21786",
        "logo_path": None,
        "bank_name": "HDFC BANK LTD",
        "bank_account_no": "99947977777777",
        "bank_ifsc": "HDFC0009254",
        "bank_branch": "Deshpande Nagar Branch, Hubli",
        "bank_upi": "svpharma@upi",
        "signatory_name": "S.V. Kumar",
        "signatory_img_path": None,
    }

    # ── Dummy customer ──
    customer = {
        "license_no": "REG NO KMC 118112",
        "shop_name": "ASHWINI SPECIALITY CLINIC",
        "license_holder_name": "DR VIVEKAND KAMAT",
        "mobile_no": "9902656680",
        "gst_no": "29AABCK9999E1ZP",
        "address": "C/O Ashwini Speciality Clinic, Near Ram Mandir, Thane Road, Dharwad, State: 29-Karnataka",
    }

    # ── Dummy invoice items ──
    items_raw = [
        {"product_name": "GLIPY DM TAB",         "batch_no": "FJ49650911", "expiry_date": date(2026, 9, 30),
         "qty": 15, "mrp": 308.80, "rate": 220.57, "discount_percent": 0,  "gst_percent": 12},
        {"product_name": "AMOXICILLIN 500MG CAP", "batch_no": "AMX2024B01", "expiry_date": date(2027, 3, 31),
         "qty": 20, "mrp": 120.50, "rate": 85.00,  "discount_percent": 5,  "gst_percent": 12},
        {"product_name": "PARACETAMOL 650MG TAB", "batch_no": "PCM650A22",  "expiry_date": date(2027, 6, 30),
         "qty": 50, "mrp": 25.00,  "rate": 15.00,  "discount_percent": 0,  "gst_percent": 5},
        {"product_name": "PANTOPRAZOLE 40MG TAB", "batch_no": "PAN40C044",  "expiry_date": date(2027, 1, 31),
         "qty": 10, "mrp": 68.50,  "rate": 45.00,  "discount_percent": 10, "gst_percent": 12},
        {"product_name": "DOLO 650 TAB",          "batch_no": "DOL650H99",  "expiry_date": date(2027, 5, 31),
         "qty": 30, "mrp": 35.00,  "rate": 20.00,  "discount_percent": 0,  "gst_percent": 5},
    ]

    # Calculate amounts per item
    for item in items_raw:
        item["amount"] = calculate_item_amount(item["qty"], item["rate"], item["discount_percent"])
        item["batch_id"] = 1  # dummy

    # Calculate invoice totals
    from decimal import Decimal, ROUND_HALF_UP
    subtotal = sum(item["amount"] for item in items_raw)
    total_discount = 0
    total_gst = 0
    for item in items_raw:
        base = item["qty"] * item["rate"]
        disc = base * item["discount_percent"] / 100
        after_disc = base - disc
        gst_val = after_disc * item["gst_percent"] / 100
        total_discount += disc
        total_gst += gst_val

    sgst = round(total_gst / 2, 2)
    cgst = round(total_gst / 2, 2)
    grand_total = round(subtotal + total_gst, 2)

    # ── Dummy invoice ──
    invoice = {
        "invoice_no": "RP00001",
        "distributor_id": 1,
        "user_id": 1,
        "customer_license_no": "REG NO KMC 118112",
        "invoice_date": date.today(),
        "payment_type": "Credit",
        "subtotal": subtotal,
        "discount_amount": round(total_discount, 2),
        "sgst": sgst,
        "cgst": cgst,
        "total_gst": round(total_gst, 2),
        "grand_total": grand_total,
        "amount_in_words": number_to_words(grand_total),
        "items": items_raw,
    }

    # ── Generate PDF ──
    from services.pdf_generator import generate_invoice_pdf, open_pdf

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"Demo_Invoice_{invoice['invoice_no']}.pdf")

    print("=" * 60)
    print("  PharmIQ — Invoice Preview Demo")
    print("=" * 60)
    print(f"  Distributor : {distributor['name']}")
    print(f"  Customer    : {customer['shop_name']}")
    print(f"  Invoice No  : {invoice['invoice_no']}")
    print(f"  Date        : {invoice['invoice_date']}")
    print(f"  Items       : {len(items_raw)}")
    print(f"  Subtotal    : Rs. {subtotal:,.2f}")
    print(f"  Discount    : Rs. {round(total_discount, 2):,.2f}")
    print(f"  SGST        : Rs. {sgst:,.2f}")
    print(f"  CGST        : Rs. {cgst:,.2f}")
    print(f"  Grand Total : Rs. {grand_total:,.2f}")
    print(f"  In Words    : {invoice['amount_in_words']}")
    print("-" * 60)

    pdf_path = generate_invoice_pdf(invoice, distributor, customer, output_path)
    print(f"\n  ✅ PDF generated: {pdf_path}")
    print(f"  📂 Opening PDF...")
    print("=" * 60)

    open_pdf(pdf_path)
    return pdf_path


if __name__ == "__main__":
    generate_demo_pdf()
