"""
Dashboard Stats Model - Aggregation queries for dashboard KPIs and charts.
"""
from db.connection import fetch_one, fetch_all

def get_kpi_stats(distributor_id):
    """Fetch Total Sales, Today's Revenue, Active Customers, Low Stock count."""
    
    # 1. Total Sales
    r1 = fetch_one("SELECT SUM(grand_total) AS total FROM invoices WHERE distributor_id = %s", (distributor_id,))
    total_sales = r1["total"] if r1 and r1["total"] else 0.0

    # 2. Today's Revenue
    r2 = fetch_one("SELECT SUM(grand_total) AS total FROM invoices WHERE distributor_id = %s AND invoice_date = CURDATE()", (distributor_id,))
    todays_revenue = r2["total"] if r2 and r2["total"] else 0.0

    # 3. Active Customers
    r3 = fetch_one("SELECT COUNT(license_no) AS count FROM customers WHERE distributor_id = %s AND status = 'active'", (distributor_id,))
    active_customers = r3["count"] if r3 and r3["count"] else 0

    # 4. Low Stock Alerts (threshold: 50 units)
    threshold = 50
    r4 = fetch_one("SELECT COUNT(batch_id) AS count FROM batches WHERE distributor_id = %s AND quantity < %s", (distributor_id, threshold))
    low_stock = r4["count"] if r4 and r4["count"] else 0

    return {
        "total_sales": total_sales,
        "todays_revenue": todays_revenue,
        "active_customers": active_customers,
        "low_stock_count": low_stock
    }

def get_sales_trend(distributor_id, limit_months=6):
    """Fetch monthly sales totals for the line chart."""
    query = """
        SELECT DATE_FORMAT(invoice_date, '%b') AS month_name,
               MONTH(invoice_date) AS m,
               YEAR(invoice_date) AS y,
               SUM(grand_total) AS total
        FROM invoices
        WHERE distributor_id = %s
        GROUP BY y, m, month_name
        ORDER BY y DESC, m DESC
        LIMIT %s
    """
    rows = fetch_all(query, (distributor_id, limit_months))
    # Reverse to get chronological order
    return list(reversed(rows))

def get_product_distribution(distributor_id):
    """
    Fetch top product categories. Since medicines table only has 'unit',
    we'll group by unit (e.g., TAB, CAP) or just grab top 4 selling items.
    Let's get top 4 selling units (categories) by quantity.
    """
    query = """
        SELECT m.unit AS category, SUM(ii.qty) AS total_qty
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.invoice_id
        JOIN batches b ON ii.batch_id = b.batch_id
        JOIN medicines m ON b.medicine_id = m.medicine_id
        WHERE i.distributor_id = %s
        GROUP BY m.unit
        ORDER BY total_qty DESC
        LIMIT 4
    """
    return fetch_all(query, (distributor_id,))

def get_low_stock_list(distributor_id, threshold=50, limit=4):
    """Fetch products with low stock for notifications."""
    query = """
        SELECT m.name AS product_name, b.batch_no, b.quantity
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.medicine_id
        WHERE b.distributor_id = %s AND b.quantity < %s
        ORDER BY b.quantity ASC
        LIMIT %s
    """
    return fetch_all(query, (distributor_id, threshold, limit))

def get_expiring_medicines(distributor_id, days_threshold=90, limit=4):
    """Fetch batches expiring within X days."""
    query = """
        SELECT m.name AS product_name, b.batch_no, b.expiry_date
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.medicine_id
        WHERE b.distributor_id = %s 
          AND b.quantity > 0 
          AND b.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
        ORDER BY b.expiry_date ASC
        LIMIT %s
    """
    return fetch_all(query, (distributor_id, days_threshold, limit))
