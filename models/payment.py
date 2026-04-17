"""
Payment model — handling customer-wise payments and FIFO allocation to invoices.
"""

from db.connection import fetch_one, fetch_all, get_connection, execute_query
from mysql.connector import Error

def record_payment(distributor_id, customer_license_no, amount, mode, date):
    """
    Record a new payment and allocate it to the oldest pending invoices (FIFO).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Insert into payments table
        cursor.execute(
            """
            INSERT INTO payments (distributor_id, customer_license_no, amount, payment_mode, payment_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (distributor_id, customer_license_no, amount, mode, date)
        )
        
        # 2. Allocate to invoices FIFO
        # Fetch pending or partial invoices for this customer ordered by date
        cursor.execute(
            """
            SELECT invoice_no, grand_total, paid_amount
            FROM invoices
            WHERE customer_license_no = %s AND status IN ('Pending', 'Partial')
            ORDER BY invoice_date ASC, created_at ASC
            """,
            (customer_license_no,)
        )
        invoices = cursor.fetchall()
        
        remaining_payment = float(amount)
        
        for inv_no, grand_total, paid_amount in invoices:
            if remaining_payment <= 0:
                break
            
            grand_total = float(grand_total)
            paid_amount = float(paid_amount)
            
            pending_on_invoice = grand_total - paid_amount
            
            if pending_on_invoice <= 0:
                continue
            
            allocation = min(remaining_payment, pending_on_invoice)
            new_paid_amount = paid_amount + allocation
            remaining_payment -= allocation
            
            # Determine new status
            if abs(new_paid_amount - grand_total) < 0.01:
                new_status = 'Paid'
            elif new_paid_amount > 0:
                new_status = 'Partial'
            else:
                new_status = 'Pending'
            
            # Update invoice
            cursor.execute(
                "UPDATE invoices SET paid_amount = %s, status = %s WHERE invoice_no = %s",
                (new_paid_amount, new_status, inv_no)
            )
            
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        print(f"[Payment] Error recording payment: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_payment_history(customer_license_no):
    """Return all payments for a customer."""
    return fetch_all(
        "SELECT * FROM payments WHERE customer_license_no = %s ORDER BY payment_date DESC, created_at DESC",
        (customer_license_no,)
    )

def get_customer_payment_summary(distributor_id):
    """
    Return aggregated payment data per customer.
    Outstanding = Total Invoiced - Total Payments
    """
    return fetch_all(
        """
        SELECT 
            c.license_no,
            c.shop_name,
            COALESCE(SUM(i.grand_total), 0) as total_invoiced,
            COALESCE((SELECT SUM(amount) FROM payments p WHERE p.customer_license_no = c.license_no), 0) as total_paid,
            (COALESCE(SUM(i.grand_total), 0) - COALESCE((SELECT SUM(amount) FROM payments p WHERE p.customer_license_no = c.license_no), 0)) as outstanding_balance
        FROM customers c
        LEFT JOIN invoices i ON c.license_no = i.customer_license_no
        WHERE c.distributor_id = %s AND c.status = 'active'
        GROUP BY c.license_no, c.shop_name
        ORDER BY outstanding_balance DESC
        """,
        (distributor_id,)
    )

def get_invoices_for_customer(customer_license_no):
    """Return all invoices for a customer with their status."""
    return fetch_all(
        "SELECT invoice_no, invoice_date, grand_total, paid_amount, status FROM invoices WHERE customer_license_no = %s ORDER BY invoice_date DESC",
        (customer_license_no,)
    )
