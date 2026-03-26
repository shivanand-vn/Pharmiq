"""
Customer model — fetch and search customers (pharmacies).
"""

from db.connection import fetch_one, fetch_all, execute_query


def get_customer_by_license(license_no):
    """Return customer dict by license_no or None."""
    return fetch_one(
        "SELECT * FROM customers WHERE license_no = %s AND status = 'active'",
        (license_no,),
    )


def search_customers(distributor_id, query=""):
    """Search customers for a distributor. Returns list of dicts."""
    like_q = f"%{query}%"
    return fetch_all(
        """
        SELECT license_no, shop_name, license_holder_name, mobile_no, gst_no, address, email, status
        FROM customers
        WHERE distributor_id = %s AND status = 'active'
          AND (shop_name LIKE %s OR license_holder_name LIKE %s OR license_no LIKE %s)
        ORDER BY shop_name
        LIMIT 20
        """,
        (distributor_id, like_q, like_q, like_q),
    )


def get_all_customers(distributor_id):
    """Return all active customers for a distributor."""
    return fetch_all(
        """
        SELECT license_no, shop_name, license_holder_name, mobile_no, gst_no, address, email, status
        FROM customers
        WHERE distributor_id = %s AND status = 'active'
        ORDER BY shop_name
        """,
        (distributor_id,),
    )

def create_customer(distributor_id, license_no, shop_name, name="", mobile="", gst="", email="", address=""):
    """Insert a new customer into the db."""
    execute_query(
        """
        INSERT INTO customers (license_no, distributor_id, shop_name, license_holder_name, mobile_no, gst_no, email, address, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """,
        (license_no, distributor_id, shop_name, name, mobile, gst, email, address)
    )

def update_customer(original_license_no, license_no, shop_name, name="", mobile="", gst="", email="", address=""):
    """Update an existing customer."""
    execute_query(
        """
        UPDATE customers 
        SET license_no=%s, shop_name=%s, license_holder_name=%s, mobile_no=%s, gst_no=%s, email=%s, address=%s
        WHERE license_no=%s
        """,
        (license_no, shop_name, name, mobile, gst, email, address, original_license_no)
    )

def toggle_customer_status(license_no, new_status):
    """Activate or deactivate a customer."""
    execute_query("UPDATE customers SET status=%s WHERE license_no=%s", (new_status, license_no))
