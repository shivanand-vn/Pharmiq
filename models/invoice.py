"""
Invoice model — CRUD for invoices and invoice items.
"""

from db.connection import fetch_one, fetch_all, get_connection
from mysql.connector import Error


def get_next_invoice_no(distributor_id):
    """
    Generate the next invoice number for a distributor, filling any gaps.
    Format: I_<3-digit sequential> — e.g. I_001, I_002
    """
    rows = fetch_all(
        "SELECT invoice_no FROM invoices WHERE distributor_id = %s",
        (distributor_id,),
    )
    used_nums = []
    for row in rows:
        inv_str = row.get("invoice_no")
        if inv_str:
            num_part = "".join(filter(str.isdigit, inv_str))
            if num_part:
                used_nums.append(int(num_part))
    
    used_nums.sort()
    next_num = 1
    for num in used_nums:
        if num == next_num:
            next_num += 1
        elif num > next_num:
            break
            
    return f"I_{next_num:03d}"


def get_next_order_no(distributor_id):
    """
    Generate the next order number based on the highest numeric order_no in the db.
    """
    rows = fetch_all(
        "SELECT order_no FROM invoices WHERE distributor_id = %s",
        (distributor_id,),
    )
    max_num = 0
    for row in rows:
        order_str = row.get("order_no")
        if order_str:
            num_part = "".join(filter(str.isdigit, order_str))
            if num_part:
                num = int(num_part)
                if num > max_num:
                    max_num = num
    
    return str(max_num + 1)


def create_invoice(invoice_data, items_data):
    """
    Create a new invoice with items in a single transaction.
    
    invoice_data: dict with keys matching invoices table columns
    items_data: list of dicts with keys matching invoice_items columns
    Returns the new invoice_no.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Insert invoice
        cursor.execute(
            """
            INSERT INTO invoices
                (invoice_no, distributor_id, user_id, customer_license_no,
                 invoice_date, payment_type,
                 subtotal, discount_amount, sgst, cgst, total_gst,
                 grand_total, amount_in_words)
            VALUES
                (%(invoice_no)s, %(distributor_id)s, %(user_id)s, %(customer_license_no)s,
                 %(invoice_date)s, %(payment_type)s,
                 %(subtotal)s, %(discount_amount)s, %(sgst)s, %(cgst)s, %(total_gst)s,
                 %(grand_total)s, %(amount_in_words)s)
            """,
            invoice_data,
        )
        invoice_no = invoice_data["invoice_no"]

        # Insert invoice items
        for item in items_data:
            item["invoice_no"] = invoice_no
            cursor.execute(
                """
                INSERT INTO invoice_items
                    (invoice_no, batch_id, product_name, batch_no, expiry_date,
                     qty, mrp, trp, discount_percent, gst_percent, amount)
                VALUES
                    (%(invoice_no)s, %(batch_id)s, %(product_name)s, %(batch_no)s,
                     %(expiry_date)s, %(qty)s, %(mrp)s, %(trp)s,
                     %(discount_percent)s, %(gst_percent)s, %(amount)s)
                """,
                item,
            )
            # Reduce batch stock
            cursor.execute(
                "UPDATE inventory_batches SET quantity = quantity - %s WHERE batch_id = %s",
                (item["qty"], item["batch_id"]),
            )

        conn.commit()
        return invoice_no
    except Error as e:
        conn.rollback()
        print(f"[Invoice] Creation error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_invoice(invoice_no):
    """Return full invoice dict with items list."""
    invoice = fetch_one(
        "SELECT * FROM invoices WHERE invoice_no = %s",
        (invoice_no,),
    )
    if invoice:
        invoice["items"] = fetch_all(
            "SELECT * FROM invoice_items WHERE invoice_no = %s ORDER BY item_id",
            (invoice_no,),
        )
    return invoice


def get_invoices_by_distributor(distributor_id, limit=50):
    """Return recent invoices list for a distributor."""
    return fetch_all(
        """
        SELECT i.invoice_no, i.invoice_date, i.grand_total,
               i.payment_type, i.status, i.paid_amount, c.shop_name AS customer_name
        FROM invoices i
        JOIN customers c ON c.license_no = i.customer_license_no
        WHERE i.distributor_id = %s
        ORDER BY i.created_at DESC
        LIMIT %s
        """,
        (distributor_id, limit),
    )

def search_invoice_history(distributor_id, query=""):
    """
    Search all invoices for a distributor using multiple criteria.
    Joins with customers to search by Shop Name, License No, or GST No.
    """
    like_q = f"%{query}%"
    return fetch_all(
        """
        SELECT i.invoice_no, i.invoice_date, i.grand_total,
               i.payment_type, i.status, i.paid_amount, c.shop_name AS customer_name,
               c.license_no, c.gst_no
        FROM invoices i
        JOIN customers c ON c.license_no = i.customer_license_no
        WHERE i.distributor_id = %s
          AND (i.invoice_no LIKE %s OR c.shop_name LIKE %s OR c.license_no LIKE %s OR c.gst_no LIKE %s)
        ORDER BY i.created_at DESC
        LIMIT 50
        """,
        (distributor_id, like_q, like_q, like_q, like_q),
    )
