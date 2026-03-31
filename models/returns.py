"""
Returns model — handles customer returns, stock updates, and item validation.
"""

from db.connection import get_connection, fetch_one, fetch_all
from mysql.connector import Error

def get_returnable_invoice(invoice_no, distributor_id):
    """
    Search for an invoice and fetch its items for return processing.
    Includes current returned_quantity and expiry validation info.
    """
    # 1. Fetch invoice info
    invoice = fetch_one(
        """
        SELECT i.invoice_id, i.invoice_no, i.customer_license_no, i.invoice_date,
               c.shop_name, c.license_holder_name
        FROM invoices i
        JOIN customers c ON i.customer_license_no = c.license_no
        WHERE i.invoice_no = %s AND i.distributor_id = %s
        """,
        (invoice_no, distributor_id)
    )
    
    if not invoice:
        return None

    # 2. Fetch items with refundable status
    items = fetch_all(
        """
        SELECT 
            item_id, product_name, batch_no, expiry_date, batch_id,
            qty as sold_qty, returned_quantity, rate, gst_percent
        FROM invoice_items
        WHERE invoice_id = %s
        """,
        (invoice['invoice_id'],)
    )
    
    invoice['items'] = items
    return invoice

def create_return(return_data, items):
    """
    Process a return in a single transaction.
    return_data: dict {invoice_id, customer_license_no, user_id, return_date, total_refund}
    items: list of dicts {invoice_item_id, batch_id, quantity, refund_amount}
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Insert return header
        cursor.execute(
            """
            INSERT INTO returns 
                (invoice_id, customer_license_no, user_id, return_date, total_refund)
            VALUES 
                (%(invoice_id)s, %(customer_license_no)s, %(user_id)s, %(return_date)s, %(total_refund)s)
            """,
            return_data
        )
        return_id = cursor.lastrowid

        # 2. Process items
        for item in items:
            item['return_id'] = return_id
            
            # Insert return item record
            cursor.execute(
                """
                INSERT INTO return_items 
                    (return_id, invoice_item_id, batch_id, quantity, refund_amount)
                VALUES 
                    (%(return_id)s, %(invoice_item_id)s, %(batch_id)s, %(quantity)s, %(refund_amount)s)
                """,
                item
            )

            # Update invoice_items.returned_quantity to track total returns against sale
            cursor.execute(
                "UPDATE invoice_items SET returned_quantity = returned_quantity + %s WHERE item_id = %s",
                (item['quantity'], item['invoice_item_id'])
            )

            # Re-increment inventory stock for the specific batch
            cursor.execute(
                "UPDATE inventory_batches SET quantity = quantity + %s WHERE batch_id = %s",
                (item['quantity'], item['batch_id'])
            )

        conn.commit()
        return return_id
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_returns_list(distributor_id, limit=50):
    """Fetch return history for a distributor."""
    return fetch_all(
        """
        SELECT r.return_id, r.return_date, r.total_refund, r.invoice_id, i.invoice_no, c.shop_name
        FROM returns r
        JOIN invoices i ON r.invoice_id = i.invoice_id
        JOIN customers c ON r.customer_license_no = c.license_no
        WHERE i.distributor_id = %s
        ORDER BY r.created_at DESC
        LIMIT %s
        """,
        (distributor_id, limit)
    )
