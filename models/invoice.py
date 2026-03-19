"""
Invoice model — CRUD for invoices and invoice items.
"""

from db.connection import fetch_one, fetch_all, get_connection
from mysql.connector import Error


def get_next_invoice_no(distributor_id):
    """
    Generate the next invoice number for a distributor.
    Format: RP<5-digit sequential> — e.g. RP00001, RP00002
    """
    row = fetch_one(
        """
        SELECT invoice_no FROM invoices
        WHERE distributor_id = %s
        ORDER BY invoice_id DESC
        LIMIT 1
        """,
        (distributor_id,),
    )
    if row and row["invoice_no"]:
        # Extract numeric part
        num_part = "".join(filter(str.isdigit, row["invoice_no"]))
        next_num = int(num_part) + 1 if num_part else 1
    else:
        next_num = 1
    return f"RP{next_num:05d}"


def create_invoice(invoice_data, items_data):
    """
    Create a new invoice with items in a single transaction.
    
    invoice_data: dict with keys matching invoices table columns
    items_data: list of dicts with keys matching invoice_items columns
    
    Returns the new invoice_id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Insert invoice
        cursor.execute(
            """
            INSERT INTO invoices
                (invoice_no, distributor_id, user_id, customer_license_no,
                 invoice_date, order_no, lr_no, transport, payment_type,
                 subtotal, discount_amount, sgst, cgst, total_gst,
                 grand_total, amount_in_words)
            VALUES
                (%(invoice_no)s, %(distributor_id)s, %(user_id)s, %(customer_license_no)s,
                 %(invoice_date)s, %(order_no)s, %(lr_no)s, %(transport)s, %(payment_type)s,
                 %(subtotal)s, %(discount_amount)s, %(sgst)s, %(cgst)s, %(total_gst)s,
                 %(grand_total)s, %(amount_in_words)s)
            """,
            invoice_data,
        )
        invoice_id = cursor.lastrowid

        # Insert invoice items
        for item in items_data:
            item["invoice_id"] = invoice_id
            cursor.execute(
                """
                INSERT INTO invoice_items
                    (invoice_id, batch_id, product_name, batch_no, expiry_date,
                     qty, mrp, rate, discount_percent, gst_percent, amount)
                VALUES
                    (%(invoice_id)s, %(batch_id)s, %(product_name)s, %(batch_no)s,
                     %(expiry_date)s, %(qty)s, %(mrp)s, %(rate)s,
                     %(discount_percent)s, %(gst_percent)s, %(amount)s)
                """,
                item,
            )
            # Reduce batch stock
            cursor.execute(
                "UPDATE batches SET quantity = quantity - %s WHERE batch_id = %s",
                (item["qty"], item["batch_id"]),
            )

        conn.commit()
        return invoice_id
    except Error as e:
        conn.rollback()
        print(f"[Invoice] Creation error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_invoice(invoice_id):
    """Return full invoice dict with items list."""
    invoice = fetch_one(
        "SELECT * FROM invoices WHERE invoice_id = %s",
        (invoice_id,),
    )
    if invoice:
        invoice["items"] = fetch_all(
            "SELECT * FROM invoice_items WHERE invoice_id = %s ORDER BY item_id",
            (invoice_id,),
        )
    return invoice


def get_invoices_by_distributor(distributor_id, limit=50):
    """Return recent invoices list for a distributor."""
    return fetch_all(
        """
        SELECT i.invoice_id, i.invoice_no, i.invoice_date, i.grand_total,
               i.payment_type, c.shop_name AS customer_name
        FROM invoices i
        JOIN customers c ON c.license_no = i.customer_license_no
        WHERE i.distributor_id = %s
        ORDER BY i.invoice_id DESC
        LIMIT %s
        """,
        (distributor_id, limit),
    )
