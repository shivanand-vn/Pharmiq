"""
Customer model — fetch and search customers (pharmacies).
"""

from db.connection import fetch_one, fetch_all


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
        SELECT license_no, shop_name, license_holder_name, mobile_no, gst_no, address
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
        SELECT license_no, shop_name, license_holder_name, mobile_no, gst_no, address
        FROM customers
        WHERE distributor_id = %s AND status = 'active'
        ORDER BY shop_name
        """,
        (distributor_id,),
    )
