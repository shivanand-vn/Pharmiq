from db.connection import get_connection
import sys

def run_migration():
    conn = get_connection()
    c = conn.cursor()
    try:
        # 1. Update invoice_items table
        print("Updating invoice_items table...")
        c.execute("SHOW COLUMNS FROM invoice_items LIKE 'returned_quantity'")
        if not c.fetchone():
            c.execute("ALTER TABLE invoice_items ADD COLUMN returned_quantity INT DEFAULT 0")
            print("  [OK] Added returned_quantity to invoice_items.")
        else:
            print("  [INFO] returned_quantity already exists in invoice_items.")

        # 2. Create returns table
        print("Creating returns table...")
        c.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                return_id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_no VARCHAR(30) NOT NULL,
                customer_license_no VARCHAR(50) NOT NULL,
                user_id INT NOT NULL,
                return_date DATE NOT NULL,
                total_refund DECIMAL(12,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_no) REFERENCES invoices(invoice_no),
                FOREIGN KEY (customer_license_no) REFERENCES customers(license_no),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            ) ENGINE=InnoDB
        """)
        print("  [OK] returns table ready.")

        # 3. Create return_items table
        print("Creating return_items table...")
        c.execute("""
            CREATE TABLE IF NOT EXISTS return_items (
                return_item_id INT AUTO_INCREMENT PRIMARY KEY,
                return_id INT NOT NULL,
                invoice_item_id INT NOT NULL,
                batch_id INT NOT NULL,
                quantity INT NOT NULL,
                refund_amount DECIMAL(12,2) NOT NULL,
                FOREIGN KEY (return_id) REFERENCES returns(return_id) ON DELETE CASCADE,
                FOREIGN KEY (invoice_item_id) REFERENCES invoice_items(item_id),
                FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id)
            ) ENGINE=InnoDB
        """)
        print("  [OK] return_items table ready.")

        conn.commit()
        print("\n--- Returns Migration successfully completed! ---")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)
    finally:
        c.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
