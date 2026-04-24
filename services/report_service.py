"""
Report Service — Config-driven report orchestration, data pipeline, and filename generation.
Provides a unified interface for fetching, processing, and exporting reports.

Architecture:
    fetch_data() → process_data() → generate_report()

New reports are added ONLY via REPORT_CONFIG — no if-else chains.
"""

import re
from datetime import datetime
from collections import defaultdict

from models.report import (
    get_sales_detail_report, get_detailed_invoice_report,
    get_inventory_report, get_expiry_report, get_returns_report
)
from models.distributor import get_distributor_by_id


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT CONFIGURATION — Single source of truth for all report types
# ═══════════════════════════════════════════════════════════════════════════════

REPORT_CONFIG = {
    "Sales Report": {
        "columns": ["Medicine Name", "Batch No", "Total Qty", "Rate (TRP)", "Total Value"],
        "column_keys": ["product_name", "batch_no", "total_qty", "trp", "total_value"],
        "currency_columns": ["Rate (TRP)", "Total Value"],
        "currency_keys": ["trp", "total_value"],
        "numeric_keys": ["total_qty", "total_value"],
        "totals_keys": {"total_qty": "Total Qty", "total_value": "Total Value"},
        "grouping": None,  # Now handled by SQL GROUP BY
    },
    "Detailed Invoice Report": {
        "columns": ["Invoice No", "Customer", "Medicine Name", "Batch No", "Qty", "Rate (TRP)", "Total", "GST %"],
        "column_keys": ["invoice_no", "customer_name", "product_name", "batch_no", "quantity", "trp", "total", "gst_percent"],
        "currency_columns": ["Rate (TRP)", "Total"],
        "currency_keys": ["trp", "total"],
        "numeric_keys": ["quantity", "total"],
        "totals_keys": {"quantity": "Qty", "total": "Total"},
        "grouping": None,
    },
    "Inventory / Stock Report": {
        "columns": ["Medicine Name", "Batch No", "Available Qty", "Expiry Date", "Cost Price", "TRP", "MRP"],
        "column_keys": ["medicine_name", "batch_no", "available_quantity", "expiry_date", "cost_price", "trp", "mrp"],
        "currency_columns": ["Cost Price", "TRP", "MRP"],
        "currency_keys": ["cost_price", "trp", "mrp"],
        "numeric_keys": ["available_quantity"],
        "totals_keys": {"available_quantity": "Available Qty"},
        "grouping": None,
    },
    "Expiry Report": {
        "columns": ["Medicine Name", "Batch No", "Expiry Date", "Available Qty"],
        "column_keys": ["medicine_name", "batch_no", "expiry_date", "quantity"],
        "currency_columns": [],
        "currency_keys": [],
        "numeric_keys": ["quantity"],
        "totals_keys": {"quantity": "Available Qty"},
        "grouping": None,
    },
    "Return Report": {
        "columns": ["Return ID", "Invoice Ref", "Medicine Name", "Batch No", "Returned Qty", "Return Date"],
        "column_keys": ["return_id", "invoice_reference", "medicine_name", "batch_no", "quantity_returned", "return_date"],
        "currency_columns": [],
        "currency_keys": [],
        "numeric_keys": ["quantity_returned"],
        "totals_keys": {"quantity_returned": "Returned Qty"},
        "grouping": None,
    },
}

# Map report types to their fetch functions
_FETCH_FUNCTIONS = {
    "Sales Report": get_sales_detail_report,
    "Detailed Invoice Report": get_detailed_invoice_report,
    "Inventory / Stock Report": get_inventory_report,
    "Expiry Report": get_expiry_report,
    "Return Report": get_returns_report,
}


def get_report_config(report_type):
    """Get configuration for a report type. Raises ValueError if not found."""
    config = REPORT_CONFIG.get(report_type)
    if not config:
        raise ValueError(f"Unknown report type: {report_type}")
    return config


# ═══════════════════════════════════════════════════════════════════════════════
# DATA PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_data(report_type, distributor_id, filters):
    """
    Fetch raw data from the database based on report type and filters.
    All filtering and aggregation happens at SQL level for performance.
    """
    fetch_fn = _FETCH_FUNCTIONS.get(report_type)
    if not fetch_fn:
        raise ValueError(f"No fetch function for report type: {report_type}")

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    customer = filters.get("customer")
    medicine = filters.get("medicine")
    expiry_days = filters.get("expiry_days", 30)

    if report_type == "Sales Report":
        return fetch_fn(distributor_id, from_date=from_date, to_date=to_date, customer_name=customer, medicine_name=medicine)

    elif report_type == "Detailed Invoice Report":
        return fetch_fn(distributor_id, from_date=from_date, to_date=to_date,
                        customer_name=customer, medicine_name=medicine)

    elif report_type == "Inventory / Stock Report":
        return fetch_fn(distributor_id, medicine_name=medicine)

    elif report_type == "Expiry Report":
        return fetch_fn(distributor_id, days=expiry_days, medicine_name=medicine,
                        from_date=from_date, to_date=to_date)

    elif report_type == "Return Report":
        return fetch_fn(distributor_id, from_date=from_date, to_date=to_date,
                        customer_name=customer, medicine_name=medicine)

    return []


def process_data(report_type, raw_data):
    """
    Process raw data — single pass normalization. 
    Grouping for Sales is now done at SQL level (GROUP BY).
    """
    config = get_report_config(report_type)
    column_keys = config["column_keys"]

    if not raw_data:
        return []

    processed = []
    for row in raw_data:
        processed_row = {}
        for key in column_keys:
            val = row.get(key, "")
            # Fallback: batch_no from batch_number for returns
            if key == "batch_no" and not val and "batch_number" in row:
                val = row["batch_number"]
            processed_row[key] = val if val is not None else ""
        processed.append(processed_row)
    return processed


def format_report_data(report_type, processed_data):
    """
    Format processed data into flat rows for UI preview and Export.
    Single pass — also computes totals.
    Returns (table_data, totals_dict).
    """
    config = get_report_config(report_type)
    column_keys = config["column_keys"]
    totals_keys = config.get("totals_keys", {})

    table_data = []
    totals = {k: 0.0 for k in totals_keys}

    for i, row in enumerate(processed_data):
        item_row = []
        for key in column_keys:
            val = row.get(key, "")
            if hasattr(val, 'strftime'):
                val = val.strftime('%Y-%m-%d')
            item_row.append(val)

        # Single-pass totals accumulation
        for tkey in totals:
            try:
                totals[tkey] += float(row.get(tkey, 0) or 0)
            except (ValueError, TypeError):
                pass

        row_tag = "even" if i % 2 == 0 else "odd"

        # Identify low stock or expiry for tags
        if report_type == "Inventory / Stock Report":
            try:
                if float(row.get("available_quantity", 0) or 0) < 10:
                    row_tag = "warning"
            except (ValueError, TypeError):
                pass
        elif report_type == "Expiry Report":
            row_tag = "danger"

        table_data.append({"is_header": False, "values": item_row, "tag": row_tag})

    return table_data, totals


# ═══════════════════════════════════════════════════════════════════════════════
# FILENAME GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_filename(report_type, from_date=None, to_date=None, customer=None, ext="xlsx"):
    """
    Generate a dynamic, sanitized filename for report export.

    Format: <ReportType>_<Customer(optional)>_<FromDate>_to_<ToDate>_<HHMMSS>.<ext>
    """
    # Clean report type: remove special chars, replace spaces with underscores
    clean_type = re.sub(r'[^a-zA-Z0-9\s]', '', report_type).strip().replace('  ', ' ').replace(' ', '_')

    parts = [clean_type]

    # Add customer if provided
    if customer and customer.strip():
        clean_customer = re.sub(r'[^a-zA-Z0-9\s]', '', customer.strip()).replace(' ', '_')
        parts.append(clean_customer)

    # Add date range
    if from_date and to_date:
        parts.append(f"{from_date}_to_{to_date}")
    elif from_date:
        parts.append(str(from_date))
    elif to_date:
        parts.append(str(to_date))
    else:
        parts.append(datetime.now().strftime('%Y-%m-%d'))

    # Add timestamp to avoid overwrites
    parts.append(datetime.now().strftime('%H%M%S'))

    return "_".join(parts) + f".{ext}"


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED REPORT CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(report_type, format_type, filters, distributor_id, file_path=None):
    """
    Unified report generation controller.
    Fetches data once, processes once, exports to the requested format.
    """
    from utils.export_reports import generate_excel_report, generate_pdf_report

    # 1. Fetch & Process Data (single pass)
    raw_data = fetch_data(report_type, distributor_id, filters)
    if not raw_data:
        return False, "No data available for the selected filters."

    processed_data = process_data(report_type, raw_data)
    table_data, totals = format_report_data(report_type, processed_data)

    config = get_report_config(report_type)
    columns = config["columns"]
    currency_columns = config.get("currency_columns", [])
    currency_keys = config.get("currency_keys", [])
    column_keys = config["column_keys"]

    # 2. Get company info for headers (single DB call)
    distributor = get_distributor_by_id(distributor_id)
    company_name = distributor.get("name", "PharmIQ") if distributor else "PharmIQ"

    # Build report title (dynamic from dropdown selection)
    report_title = report_type

    # Build date range string
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if from_date and to_date:
        date_range = f"From {from_date} to {to_date}"
    elif from_date:
        date_range = f"From {from_date}"
    elif to_date:
        date_range = f"Up to {to_date}"
    else:
        date_range = f"Generated on {datetime.now().strftime('%Y-%m-%d')}"

    # Create file path if not provided
    if not file_path:
        file_name = generate_filename(report_type, from_date, to_date, filters.get("customer"), ext=format_type)
        file_path = file_name

    # Build totals row
    totals_row = []
    for i, key in enumerate(column_keys):
        if key in config.get("totals_keys", {}):
            totals_row.append(totals.get(key, ""))
        elif i == 0:
            totals_row.append("TOTAL")
        else:
            totals_row.append("")

    header_info = {
        "company_name": company_name,
        "address": distributor.get("address", "") if distributor else "",
        "phone": distributor.get("mobile_no", "") if distributor else "",
        "email": distributor.get("email", "") if distributor else "",
        "gst_no": distributor.get("gst_no", "") if distributor else "",
        "licence_no": distributor.get("drug_license_no", "") if distributor else "",
        "report_title": report_title,
        "date_range": date_range,
        "customer_filter": filters.get("customer", ""),
        "medicine_filter": filters.get("medicine", ""),
    }

    if format_type == "xlsx":
        return generate_excel_report(columns, table_data, file_path, header_info, currency_columns, totals_row)
    elif format_type == "pdf":
        return generate_pdf_report(columns, table_data, file_path, header_info, currency_columns, totals_row)
    else:
        return False, f"Unsupported format type: {format_type}"
