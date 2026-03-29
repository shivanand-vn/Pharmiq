"""
Product / Batch model — search medicines and available batches.
"""

from db.connection import fetch_all


def search_products(distributor_id, query=""):
    """Search medicines with available batches for a distributor."""
    like_q = f"%{query}%"
    return fetch_all(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit,
            m.gst_percent,
            b.batch_no,
            b.expiry_date,
            b.quantity AS available_qty,
            b.purchase_price,
            b.mrp,
            b.selling_price,
            b.discount_percent
        FROM batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        WHERE b.distributor_id = %s
          AND b.quantity > 0
          AND (m.name LIKE %s OR b.batch_no LIKE %s)
        ORDER BY m.name, b.expiry_date
        LIMIT 30
        """,
        (distributor_id, like_q, like_q),
    )


def get_batch_by_id(batch_id):
    """Return batch with medicine info."""
    from db.connection import fetch_one
    return fetch_one(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit,
            m.gst_percent,
            b.batch_no,
            b.expiry_date,
            b.quantity AS available_qty,
            b.purchase_price,
            b.mrp,
            b.selling_price,
            b.discount_percent
        FROM batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        WHERE b.batch_id = %s
        """,
        (batch_id,),
    )


def get_all_products_for_distributor(distributor_id):
    """Return all products with available stock for a distributor."""
    return fetch_all(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit,
            m.gst_percent,
            b.batch_no,
            b.expiry_date,
            b.quantity AS available_qty,
            b.purchase_price,
            b.mrp,
            b.selling_price,
            b.discount_percent
        FROM batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        WHERE b.distributor_id = %s AND b.quantity > 0
        ORDER BY m.name, b.expiry_date
        """,
        (distributor_id,),
    )


def get_inventory_list(distributor_id, search_q=""):
    """Return all inventory for a distributor matching the search query."""
    like_q = f"%{search_q}%"
    return fetch_all(
        """
        SELECT
            b.batch_id,
            m.name AS product_name,
            m.unit AS category,
            s.name AS supplier_name,
            b.batch_no,
            b.expiry_date,
            b.quantity,
            b.purchase_price,
            b.mrp,
            b.selling_price,
            b.discount_percent
        FROM batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        LEFT JOIN suppliers s ON b.supplier_id = s.supplier_id
        WHERE b.distributor_id = %s
          AND (m.name LIKE %s OR b.batch_no LIKE %s)
        ORDER BY m.name ASC
        """,
        (distributor_id, like_q, like_q),
    )


def update_medicine_pricing(batch_id, selling_price, mrp, discount_percent):
    """
    ENFORCED UPDATE: Update ONLY pricing fields for a medicine.
    Rejects any attempts to change stock, batch, or expiry.
    """
    from db.connection import execute_query
    return execute_query(
        """
        UPDATE batches 
        SET selling_price = %s, mrp = %s, discount_percent = %s
        WHERE batch_id = %s
        """,
        (selling_price, mrp, discount_percent, batch_id)
    )


def update_inventory_batch(batch_id, medicine_id, supplier_id, batch_no, expiry_date, quantity, purchase_price, mrp):
    """Full update for inventory management module."""
    from db.connection import execute_query
    return execute_query(
        """
        UPDATE batches
        SET medicine_id = %s, supplier_id = %s, batch_no = %s, expiry_date = %s,
            quantity = %s, purchase_price = %s, mrp = %s
        WHERE batch_id = %s
        """,
        (medicine_id, supplier_id, batch_no, expiry_date, quantity, purchase_price, mrp, batch_id)
    )
