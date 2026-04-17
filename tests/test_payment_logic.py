"""
Verification script for FIFO payment logic.
"""
from db.connection import get_connection, execute_query, fetch_all, fetch_one
from models.payment import record_payment
from models.invoice import create_invoice
import datetime

def test_fifo():
    # Setup test customer if not exists
    license_no = "TEST_CUST_FIFO"
    distributor_id = 1 # Assuming dist 1 exists from seed data
    user_id = 1
    
    # Clean up previous tests
    execute_query("DELETE FROM payments WHERE customer_license_no = %s", (license_no,))
    execute_query("DELETE FROM invoices WHERE customer_license_no = %s", (license_no,))
    execute_query("DELETE FROM customers WHERE license_no = %s", (license_no,))
    
    # Create customer
    execute_query(
        "INSERT INTO customers (license_no, distributor_id, shop_name, gst_no, address_line1, city, dist, state, pincode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (license_no, distributor_id, "FIFO Test Shop", "GST_FIFO_123", "Street 1", "City", "Dist", "State", "123456")
    )
    
    print("Created test customer.")
    
    # Create two invoices
    # Inv 1: 5000
    # Inv 2: 3000
    inv1_data = {
        "invoice_no": "T_INV_001", "distributor_id": distributor_id, "user_id": user_id,
        "customer_license_no": license_no, "invoice_date": "2023-01-01", "payment_type": "Credit",
        "subtotal": 5000, "discount_amount": 0, "sgst": 0, "cgst": 0, "total_gst": 0,
        "grand_total": 5000, "amount_in_words": "Five Thousand"
    }
    inv2_data = {
        "invoice_no": "T_INV_002", "distributor_id": distributor_id, "user_id": user_id,
        "customer_license_no": license_no, "invoice_date": "2023-02-01", "payment_type": "Credit",
        "subtotal": 3000, "discount_amount": 0, "sgst": 0, "cgst": 0, "total_gst": 0,
        "grand_total": 3000, "amount_in_words": "Three Thousand"
    }
    
    # We bypass create_invoice to avoid batch stock dependency in this simple test
    execute_query(
        """
        INSERT INTO invoices (invoice_no, distributor_id, user_id, customer_license_no, invoice_date, grand_total, status)
        VALUES (%(invoice_no)s, %(distributor_id)s, %(user_id)s, %(customer_license_no)s, %(invoice_date)s, %(grand_total)s, 'Pending')
        """,
        inv1_data
    )
    execute_query(
        """
        INSERT INTO invoices (invoice_no, distributor_id, user_id, customer_license_no, invoice_date, grand_total, status)
        VALUES (%(invoice_no)s, %(distributor_id)s, %(user_id)s, %(customer_license_no)s, %(invoice_date)s, %(grand_total)s, 'Pending')
        """,
        inv2_data
    )
    
    print("Created two invoices: T_INV_001 (5000) and T_INV_002 (3000).")
    
    # Record payment of 6000
    # Expected: Inv 1 (5000) -> Paid, Inv 2 (1000 paid) -> Partial
    print("Recording payment of 6000...")
    record_payment(distributor_id, license_no, 6000, "Cash", "2023-03-01")
    
    # Verify
    res1 = fetch_one("SELECT paid_amount, status FROM invoices WHERE invoice_no = 'T_INV_001'")
    res2 = fetch_one("SELECT paid_amount, status FROM invoices WHERE invoice_no = 'T_INV_002'")
    
    print(f"Result T_INV_001: Paid={res1['paid_amount']}, Status={res1['status']}")
    print(f"Result T_INV_002: Paid={res2['paid_amount']}, Status={res2['status']}")
    
    assert float(res1['paid_amount']) == 5000
    assert res1['status'] == 'Paid'
    assert float(res2['paid_amount']) == 1000
    assert res2['status'] == 'Partial'
    
    print("\n[SUCCESS] FIFO Logic verified!")

if __name__ == "__main__":
    try:
        test_fifo()
    except Exception as e:
        print(f"\n[FAILURE] {e}")
