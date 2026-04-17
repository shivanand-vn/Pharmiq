"""Migration script to add payments support."""
from db.connection import get_connection
from mysql.connector import Error

def migrate():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        print("Checking invoices table...")
        # Add columns to invoices if they don't exist
        cursor.execute("SHOW COLUMNS FROM invoices LIKE 'paid_amount'")
        if not cursor.fetchone():
            print("Adding paid_amount column to invoices...")
            cursor.execute("ALTER TABLE invoices ADD COLUMN paid_amount DECIMAL(12,2) DEFAULT 0.00 AFTER grand_total")
        
        cursor.execute("SHOW COLUMNS FROM invoices LIKE 'status'")
        if not cursor.fetchone():
            print("Adding status column to invoices...")
            cursor.execute("ALTER TABLE invoices ADD COLUMN status ENUM('Pending', 'Partial', 'Paid') DEFAULT 'Pending' AFTER paid_amount")

        print("Creating payments table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                distributor_id INT NOT NULL,
                customer_license_no VARCHAR(50) NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                payment_mode ENUM('Cash', 'UPI', 'Bank') NOT NULL,
                payment_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id),
                FOREIGN KEY (customer_license_no) REFERENCES customers(license_no)
            ) ENGINE=InnoDB
        """)

        conn.commit()
        print("\n=== Migration complete successfully! ===")
    except Error as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
