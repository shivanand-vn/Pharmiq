"""
Invoice service — business logic for invoice creation and calculations.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from models.invoice import get_next_invoice_no, create_invoice, get_invoice
from utils.num_to_words import number_to_words


def calculate_item_amount(qty, rate, discount_percent):
    """Calculate the amount for a single line item (before GST)."""
    try:
        q = Decimal(str(qty))
        r = Decimal(str(rate))
        d = Decimal(str(discount_percent))
        base = q * r
        discount = (base * d / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return float((base - discount).quantize(Decimal("0.01"), ROUND_HALF_UP))
    except Exception:
        return 0.0


def calculate_invoice_totals(items):
    """
    Given a list of item dicts (each with qty, rate, discount_percent, gst_percent, amount),
    compute the invoice-level totals.

    Returns dict with: subtotal, discount_amount, sgst, cgst, total_gst, grand_total
    """
    try:
        subtotal = Decimal("0")
        total_discount = Decimal("0")
        total_gst = Decimal("0")

        for item in items:
            q = Decimal(str(item["qty"]))
            r = Decimal(str(item["rate"]))
            d = Decimal(str(item.get("discount_percent", 0)))
            g = Decimal(str(item.get("gst_percent", 0)))

            base = q * r
            discount = (base * d / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
            after_disc = base - discount
            gst_val = (after_disc * g / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)

            subtotal += after_disc
            total_discount += discount
            total_gst += gst_val

        sgst = (total_gst / Decimal("2")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        cgst = (total_gst / Decimal("2")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        grand_total = (subtotal + total_gst).quantize(Decimal("0.01"), ROUND_HALF_UP)

        return {
            "subtotal": float(subtotal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "discount_amount": float(total_discount.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "sgst": float(sgst),
            "cgst": float(cgst),
            "total_gst": float(total_gst.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "grand_total": float(grand_total),
        }
    except Exception:
        return {
            "subtotal": 0.0,
            "discount_amount": 0.0,
            "sgst": 0.0,
            "cgst": 0.0,
            "total_gst": 0.0,
            "grand_total": 0.0,
        }


def build_gst_summary(items):
    """
    Group items by GST slab and return summary rows.
    Returns list of dicts: [{gst_percent, taxable_amount, sgst, cgst, total_gst}, ...]
    """
    slabs = {}
    for item in items:
        g = float(item.get("gst_percent", 0))
        amount = float(item.get("amount", 0))
        if g not in slabs:
            slabs[g] = {"gst_percent": g, "taxable_amount": 0.0}
        slabs[g]["taxable_amount"] += amount

    result = []
    for pct, data in sorted(slabs.items()):
        taxable = round(data["taxable_amount"], 2)
        gst_val = round(taxable * pct / 100, 2)
        result.append({
            "gst_percent": pct,
            "taxable_amount": taxable,
            "sgst": round(gst_val / 2, 2),
            "cgst": round(gst_val / 2, 2),
            "total_gst": gst_val,
        })
    return result


def create_full_invoice(distributor_id, user_id, customer_license_no,
                         items, order_no="", lr_no="", transport="",
                         payment_type="Credit", invoice_date=None):
    """
    High-level function: compute totals, generate invoice number,
    create invoice + items in DB. Returns the created invoice dict.

    items: list of dicts with keys:
        batch_id, product_name, batch_no, expiry_date, qty, mrp, rate,
        discount_percent, gst_percent
    """
    # Calculate per-item amounts
    for item in items:
        item["amount"] = calculate_item_amount(
            item["qty"], item["rate"], item.get("discount_percent", 0)
        )

    # Calculate totals
    totals = calculate_invoice_totals(items)

    # Generate invoice number
    invoice_no = get_next_invoice_no(distributor_id)

    # Amount in words
    amount_words = number_to_words(totals["grand_total"])

    if not invoice_date:
        invoice_date = date.today().strftime("%Y-%m-%d")

    # Build invoice data
    invoice_data = {
        "invoice_no": invoice_no,
        "distributor_id": distributor_id,
        "user_id": user_id,
        "customer_license_no": customer_license_no,
        "invoice_date": invoice_date,
        "order_no": order_no,
        "lr_no": lr_no,
        "transport": transport,
        "payment_type": payment_type,
        "subtotal": totals["subtotal"],
        "discount_amount": totals["discount_amount"],
        "sgst": totals["sgst"],
        "cgst": totals["cgst"],
        "total_gst": totals["total_gst"],
        "grand_total": totals["grand_total"],
        "amount_in_words": amount_words,
    }

    # Create in DB
    invoice_id = create_invoice(invoice_data, items)

    # Return full invoice
    return get_invoice(invoice_id)
