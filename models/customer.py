"""
Customer model — fetch, search, create, and update customers (pharmacies).
Supports structured address fields.
"""

from db.connection import fetch_one, fetch_all, execute_query


def check_gst_exists(gst_no, exclude_license=None):
    """Check if a GST number already exists. Optionally exclude a license_no (for edits)."""
    if exclude_license:
        row = fetch_one(
            "SELECT license_no FROM customers WHERE gst_no = %s AND license_no != %s AND status = 'active'",
            (gst_no, exclude_license)
        )
    else:
        row = fetch_one(
            "SELECT license_no FROM customers WHERE gst_no = %s AND status = 'active'",
            (gst_no,)
        )
    return row is not None


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
        SELECT license_no, shop_name, license_holder_name, mobile_no, gst_no,
               address_line1, address_line2, city, dist, state, pincode, country,
               email, status
        FROM customers
        WHERE distributor_id = %s AND status = 'active'
          AND (shop_name LIKE %s OR license_holder_name LIKE %s OR license_no LIKE %s OR mobile_no LIKE %s)
        ORDER BY shop_name
        LIMIT 50
        """,
        (distributor_id, like_q, like_q, like_q, like_q),
    )


def get_all_customers(distributor_id):
    """Return all active customers for a distributor."""
    return fetch_all(
        """
        SELECT license_no, shop_name, license_holder_name, mobile_no, gst_no,
               address_line1, address_line2, city, dist, state, pincode, country,
               email, status
        FROM customers
        WHERE distributor_id = %s AND status = 'active'
        ORDER BY shop_name
        LIMIT 50
        """,
        (distributor_id,),
    )


def create_customer(distributor_id, license_no, shop_name, name="", mobile="",
                     gst="", email="", address_line1="", address_line2="",
                     city="", dist="", state="", pincode="", country="India"):
    """Insert a new customer into the db with structured address."""
    execute_query(
        """
        INSERT INTO customers
            (license_no, distributor_id, shop_name, license_holder_name,
             mobile_no, gst_no, email,
             address_line1, address_line2, city, dist, state, pincode, country, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """,
        (license_no, distributor_id, shop_name, name,
         mobile, gst, email,
         address_line1, address_line2, city, dist, state, pincode, country)
    )


def update_customer(original_license_no, license_no, shop_name, name="", mobile="",
                     gst="", email="", address_line1="", address_line2="",
                     city="", dist="", state="", pincode="", country="India"):
    """Update an existing customer with structured address."""
    if license_no.strip().upper() == original_license_no.strip().upper():
        # License unchanged — skip PK update to avoid FK constraint issues
        execute_query(
            """
            UPDATE customers
            SET shop_name=%s, license_holder_name=%s,
                mobile_no=%s, gst_no=%s, email=%s,
                address_line1=%s, address_line2=%s, city=%s, dist=%s,
                state=%s, pincode=%s, country=%s
            WHERE license_no=%s
            """,
            (shop_name, name,
             mobile, gst, email,
             address_line1, address_line2, city, dist, state, pincode, country,
             original_license_no)
        )
    else:
        # License changed — update everything
        execute_query(
            """
            UPDATE customers
            SET license_no=%s, shop_name=%s, license_holder_name=%s,
                mobile_no=%s, gst_no=%s, email=%s,
                address_line1=%s, address_line2=%s, city=%s, dist=%s,
                state=%s, pincode=%s, country=%s
            WHERE license_no=%s
            """,
            (license_no, shop_name, name,
             mobile, gst, email,
             address_line1, address_line2, city, dist, state, pincode, country,
             original_license_no)
        )


def toggle_customer_status(license_no, new_status):
    """Activate or deactivate a customer."""
    execute_query("UPDATE customers SET status=%s WHERE license_no=%s", (new_status, license_no))
