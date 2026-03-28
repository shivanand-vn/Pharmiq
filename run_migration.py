"""Run the customer address migration."""
from db.connection import get_connection

conn = get_connection()
c = conn.cursor()

try:
    # Add new columns
    c.execute("ALTER TABLE customers ADD COLUMN address_line1 VARCHAR(255) NOT NULL DEFAULT '' AFTER email")
    c.execute("ALTER TABLE customers ADD COLUMN address_line2 VARCHAR(255) DEFAULT NULL AFTER address_line1")
    c.execute("ALTER TABLE customers ADD COLUMN city VARCHAR(100) NOT NULL DEFAULT '' AFTER address_line2")
    c.execute("ALTER TABLE customers ADD COLUMN dist VARCHAR(100) NOT NULL DEFAULT '' AFTER city")
    c.execute("ALTER TABLE customers ADD COLUMN state VARCHAR(100) NOT NULL DEFAULT '' AFTER dist")
    c.execute("ALTER TABLE customers ADD COLUMN pincode VARCHAR(10) NOT NULL DEFAULT '' AFTER state")
    c.execute("ALTER TABLE customers ADD COLUMN country VARCHAR(50) NOT NULL DEFAULT 'India' AFTER pincode")
    print("[OK] New columns added.")

    # Migrate existing address data
    c.execute("UPDATE customers SET address_line1 = COALESCE(address, '') WHERE address IS NOT NULL AND address_line1 = ''")
    print("[OK] Existing address data migrated to address_line1.")

    # Drop old column
    c.execute("ALTER TABLE customers DROP COLUMN address")
    print("[OK] Old address column dropped.")

    conn.commit()
    print("\n=== Migration complete! ===")

    # Verify
    c.execute("DESCRIBE customers")
    print("\nNew table structure:")
    for r in c.fetchall():
        print(f"  {r[0]:20s} {r[1]}")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] Migration failed: {e}")
finally:
    c.close()
    conn.close()
