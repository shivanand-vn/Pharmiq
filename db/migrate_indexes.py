import mysql.connector
from db.connection import get_connection

def apply_indexes():
    conn = get_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    cursor = conn.cursor()

    indexes = [
        ("idx_customers_shop_name", "customers", "shop_name(50)"),
        ("idx_customers_mobile_no", "customers", "mobile_no"),
        ("idx_invoices_customer_license", "invoices", "customer_license_no"),
        ("idx_invoices_invoice_date", "invoices", "invoice_date"),
        ("idx_invoices_status", "invoices", "status")
    ]

    for index_name, table, column in indexes:
        try:
            # Check if index exists first to prevent errors
            cursor.execute(f"SHOW INDEX FROM {table} WHERE Key_name = '{index_name}'")
            if cursor.fetchone():
                print(f"Index {index_name} already exists on {table}.")
            else:
                print(f"Creating index {index_name} on {table}({column})...")
                cursor.execute(f"CREATE INDEX {index_name} ON {table}({column})")
                print(f"Success.")
        except mysql.connector.Error as e:
            print(f"Error creating index {index_name}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    apply_indexes()
