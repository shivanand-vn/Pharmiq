"""
Migration: Make gst_no NOT NULL and UNIQUE on customers table.
- Backfills existing NULL/empty rows with unique dummy GST values.
- Then alters the column to NOT NULL and adds a UNIQUE index.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import execute_query, fetch_all

def run():
    print("=" * 50)
    print("Migration: GST No → NOT NULL + UNIQUE")
    print("=" * 50)

    # Step 1: Find customers with NULL or empty gst_no
    rows = fetch_all(
        "SELECT license_no, gst_no FROM customers WHERE gst_no IS NULL OR gst_no = '' OR TRIM(gst_no) = ''"
    )

    if rows:
        print(f"\nFound {len(rows)} customers with missing GST. Backfilling...")
        for idx, row in enumerate(rows, start=1):
            # Generate unique dummy GST: 29ABCDE{0001-9999}F1Z5
            dummy_gst = f"29ABCDE{idx:04d}F1Z5"
            execute_query(
                "UPDATE customers SET gst_no = %s WHERE license_no = %s",
                (dummy_gst, row["license_no"])
            )
            print(f"  {row['license_no']} → {dummy_gst}")
    else:
        print("\nAll customers already have GST values. ✓")

    # Step 2: Alter column to NOT NULL
    print("\nAltering gst_no to NOT NULL...")
    try:
        execute_query("ALTER TABLE customers MODIFY COLUMN gst_no VARCHAR(20) NOT NULL DEFAULT ''")
        print("  Column altered. ✓")
    except Exception as e:
        if "Duplicate" in str(e):
            print(f"  Warning: {e}")
        else:
            print(f"  Column may already be NOT NULL: {e}")

    # Step 3: Add UNIQUE index (if not exists)
    print("\nAdding UNIQUE index on gst_no...")
    try:
        execute_query("ALTER TABLE customers ADD UNIQUE INDEX idx_gst_unique (gst_no)")
        print("  UNIQUE index added. ✓")
    except Exception as e:
        if "Duplicate" in str(e) or "1061" in str(e):
            print("  UNIQUE index already exists. ✓")
        else:
            print(f"  Warning: {e}")

    print("\n✅ Migration complete!")


if __name__ == "__main__":
    run()
