"""
Report model — logic for querying and aggregating data for the Reports module.
"""

from db.connection import fetch_all
from datetime import datetime, timedelta

def get_sales_report(distributor_id, from_date=None, to_date=None, customer_name=None, status=None):
    """
    Invoice-wise sales report.
    Fields: Invoice No, Date, Customer Name, Total Amount, Payment Status.
    """
    query = """
        SELECT i.invoice_no, i.invoice_date, c.shop_name as customer_name, i.grand_total, i.payment_type as status
        FROM invoices i
        LEFT JOIN customers c ON i.customer_license_no = c.license_no
        WHERE i.distributor_id = %s
    """
    params = [distributor_id]

    if from_date:
        query += " AND i.invoice_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND i.invoice_date <= %s"
        params.append(to_date)
    if customer_name:
        query += " AND c.shop_name LIKE %s"
        params.append(f"%{customer_name}%")
    if status and status != 'All':
        query += " AND i.payment_type = %s"
        params.append(status)

    query += " ORDER BY i.invoice_date DESC, i.invoice_no DESC"
    return fetch_all(query, tuple(params))

def get_detailed_invoice_report(distributor_id, from_date=None, to_date=None, customer_name=None, medicine_name=None):
    """
    Detailed item-wise invoice report.
    Fields: Invoice Number, Customer, Medicine Name, Batch Number, Quantity, Rate, Total, GST (Total GST).
    """
    query = """
        SELECT i.invoice_no, c.shop_name as customer_name, ii.product_name, ii.batch_no, ii.qty as quantity,
               ii.trp, ii.amount as total, ii.gst_percent
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_no = i.invoice_no
        LEFT JOIN customers c ON i.customer_license_no = c.license_no
        WHERE i.distributor_id = %s
    """
    params = [distributor_id]

    if from_date:
        query += " AND i.invoice_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND i.invoice_date <= %s"
        params.append(to_date)
    if customer_name:
        query += " AND c.shop_name LIKE %s"
        params.append(f"%{customer_name}%")
    if medicine_name:
        query += " AND ii.product_name LIKE %s"
        params.append(f"%{medicine_name}%")

    query += " ORDER BY i.invoice_date DESC, i.invoice_no DESC"
    return fetch_all(query, tuple(params))

def get_inventory_report(distributor_id, medicine_name=None):
    """
    Inventory/Stock report.
    Fields: Medicine Name, Batch Number, Available Quantity, Expiry Date, Purchase Price, Selling Price.
    """
    query = """
        SELECT m.name as medicine_name, b.batch_number as batch_no, b.quantity as available_quantity,
               b.expiry_date, b.purchase_price as cost_price, m.trp, m.mrp
        FROM inventory_batches b
        LEFT JOIN medicines m ON b.medicine_id = m.medicine_id
        WHERE b.distributor_id = %s
    """
    params = [distributor_id]

    if medicine_name:
        query += " AND m.name LIKE %s"
        params.append(f"%{medicine_name}%")

    query += " ORDER BY m.name ASC, b.expiry_date ASC"
    
    # Fallback to older tables if the above query fails (Pharmiq schema seems to just have batches and medicines directly)
    try:
        return fetch_all(query, tuple(params))
    except (Exception) as e:
        # Fallback schema query:
        fallback_query = """
            SELECT m.name as medicine_name, b.batch_number as batch_no, b.quantity as available_quantity,
                   b.expiry_date, b.purchase_price as cost_price, m.trp, m.mrp
            FROM inventory_batches b
            JOIN medicines m ON b.medicine_id = m.medicine_id
            WHERE b.distributor_id = %s
        """
        if medicine_name:
            fallback_query += " AND m.name LIKE %s"
            params = [distributor_id, f"%{medicine_name}%"]
            
        fallback_query += " ORDER BY m.name ASC, b.expiry_date ASC"
        return fetch_all(fallback_query, tuple(params))

def get_expiry_report(distributor_id, days=30, medicine_name=None):
    """
    Expiry report.
    Fields: Medicine Name, Batch Number, Expiry Date, Quantity.
    """
    params = [distributor_id]
    
    # Compute the cutoff date
    if type(days) == str:
        try:
            days = int(days)
        except ValueError:
            days = 30
    
    cutoff_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    params.append(cutoff_date)

    query = """
        SELECT m.name as medicine_name, b.batch_number as batch_no, b.expiry_date, b.quantity
        FROM inventory_batches b
        JOIN medicines m ON b.medicine_id = m.medicine_id
        WHERE b.distributor_id = %s AND b.expiry_date <= %s AND b.quantity > 0
    """

    if medicine_name:
        query += " AND m.name LIKE %s"
        params.append(f"%{medicine_name}%")

    query += " ORDER BY b.expiry_date ASC"
    return fetch_all(query, tuple(params))

def get_returns_report(distributor_id, from_date=None, to_date=None, customer_name=None, medicine_name=None):
    """
    Customer Returns report.
    Fields: Return ID, Invoice Reference, Medicine Name, Batch Number, Quantity Returned, Return Date.
    """
    query = """
        SELECT r.return_id, i.invoice_no as invoice_reference, ii.product_name as medicine_name, 
               ri.batch_id, ri.quantity as quantity_returned, r.return_date, 
               b.batch_number as batch_no
        FROM returns r
        JOIN return_items ri ON r.return_id = ri.return_id
        JOIN invoice_items ii ON ri.invoice_item_id = ii.item_id
        JOIN invoices i ON r.invoice_no = i.invoice_no
        JOIN customers c ON r.customer_license_no = c.license_no
        LEFT JOIN inventory_batches b ON ri.batch_id = b.batch_id
        WHERE i.distributor_id = %s
    """
    params = [distributor_id]

    if from_date:
        query += " AND r.return_date >= %s"
        params.append(from_date)
    if to_date:
        query += " AND r.return_date <= %s"
        params.append(to_date)
    if customer_name:
        query += " AND c.shop_name LIKE %s"
        params.append(f"%{customer_name}%")
    if medicine_name:
        query += " AND ii.product_name LIKE %s"
        params.append(f"%{medicine_name}%")

    query += " ORDER BY r.return_date DESC"
    return fetch_all(query, tuple(params))
