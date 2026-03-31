"""
Product / Inventory Batch model — handles stock management and medicine pricing.
Refactored to support batch-wise merging and medicine-level pricing.
"""

from db.connection import fetch_all, fetch_one, execute_query


def search_products(distributor_id, query=""):
    """Search medicines with available stock for a distributor."""
    like_q = f"%{query}%"
    return fetch_all(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit,
            m.gst_percent,
            b.batch_number,
            b.expiry_date,
            b.quantity AS available_qty,
            b.purchase_price,
            m.mrp,
            m.selling_price,
            m.discount_percent
        FROM inventory_batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        WHERE b.distributor_id = %s
          AND b.quantity > 0
          AND (m.name LIKE %s OR b.batch_number LIKE %s)
        ORDER BY m.name, b.expiry_date
        LIMIT 30
        """,
        (distributor_id, like_q, like_q),
    )


def get_batch_by_id(batch_id):
    """Return specific inventory batch with medicine info."""
    return fetch_one(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit,
            m.gst_percent,
            b.batch_number,
            b.expiry_date,
            b.quantity AS available_qty,
            b.purchase_price,
            m.mrp,
            m.selling_price,
            m.discount_percent
        FROM inventory_batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        WHERE b.batch_id = %s
        """,
        (batch_id,),
    )


def get_all_products_for_distributor(distributor_id):
    """Return all items with available stock for a distributor."""
    return fetch_all(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit,
            m.gst_percent,
            b.batch_number,
            b.expiry_date,
            b.quantity AS available_qty,
            b.purchase_price,
            m.mrp,
            m.selling_price,
            m.discount_percent
        FROM inventory_batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        WHERE b.distributor_id = %s AND b.quantity > 0
        ORDER BY m.name, b.expiry_date
        """,
        (distributor_id,),
    )


def get_inventory_list(distributor_id, search_q=""):
    """Return detailed inventory list for management UI."""
    like_q = f"%{search_q}%"
    return fetch_all(
        """
        SELECT
            b.batch_id,
            m.medicine_id,
            m.name AS product_name,
            m.unit AS category,
            s.name AS supplier_name,
            b.batch_number,
            b.expiry_date,
            b.quantity,
            b.purchase_price,
            m.mrp,
            m.selling_price,
            m.discount_percent
        FROM inventory_batches b
        JOIN medicines m ON m.medicine_id = b.medicine_id
        LEFT JOIN suppliers s ON b.supplier_id = s.supplier_id
        WHERE b.distributor_id = %s
          AND (m.name LIKE %s OR b.batch_number LIKE %s)
        ORDER BY b.expiry_date ASC, m.name ASC
        """,
        (distributor_id, like_q, like_q),
    )


def check_batch_exists(distributor_id, medicine_id, batch_number):
    """Check if a batch already exists for a medicine."""
    return fetch_one(
        "SELECT * FROM inventory_batches WHERE distributor_id = %s AND medicine_id = %s AND batch_number = %s",
        (distributor_id, medicine_id, batch_number)
    )


def add_new_stock(distributor_id, medicine_id, supplier_id, batch_number, expiry_date, quantity, purchase_price):
    """Insert a new stock entry."""
    return execute_query(
        """
        INSERT INTO inventory_batches 
        (distributor_id, medicine_id, supplier_id, batch_number, expiry_date, quantity, purchase_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (distributor_id, medicine_id, supplier_id, batch_number, expiry_date, quantity, purchase_price)
    )


def update_existing_stock_qty(batch_id, additional_qty, purchase_price=None):
    """Increase quantity of an existing batch. Optionally update purchase price."""
    if purchase_price:
        return execute_query(
            "UPDATE inventory_batches SET quantity = quantity + %s, purchase_price = %s WHERE batch_id = %s",
            (additional_qty, purchase_price, batch_id)
        )
    return execute_query(
        "UPDATE inventory_batches SET quantity = quantity + %s WHERE batch_id = %s",
        (additional_qty, batch_id)
    )


def update_medicine_pricing(medicine_id, selling_price, mrp, discount_percent):
    """Update pricing on the medicine level."""
    return execute_query(
        "UPDATE medicines SET selling_price = %s, mrp = %s, discount_percent = %s WHERE medicine_id = %s",
        (selling_price, mrp, discount_percent, medicine_id)
    )


def update_inventory_batch_details(batch_id, supplier_id, batch_number, expiry_date, purchase_price):
    """Update non-quantity details of a batch (Admin only/Controlled flow)."""
    return execute_query(
        """
        UPDATE inventory_batches
        SET supplier_id = %s, batch_number = %s, expiry_date = %s, purchase_price = %s
        WHERE batch_id = %s
        """,
        (supplier_id, batch_number, expiry_date, purchase_price, batch_id)
    )
