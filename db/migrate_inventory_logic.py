from db.connection import get_connection
import sys

def run_migration():
    conn = get_connection()
    c = conn.cursor()
    try:
        # 1. Update medicines table
        print("Updating medicines table columns...")
        
        def add_column_if_not_exists(table, column, definition):
            c.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
            if not c.fetchone():
                c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                print(f"  [OK] Added {column} to {table}.")
            else:
                print(f"  [INFO] {column} already exists in {table}.")

        add_column_if_not_exists('medicines', 'selling_price', 'DECIMAL(10,2) DEFAULT 0.00')
        add_column_if_not_exists('medicines', 'mrp', 'DECIMAL(10,2) DEFAULT 0.00')
        add_column_if_not_exists('medicines', 'discount_percent', 'DECIMAL(5,2) DEFAULT 0.00')

        # 2. Migrate data from batches to medicines
        # We take the MAX pricing for each medicine to avoid data loss
        print("Migrating pricing data from batches to medicines...")
        
        # Check which table name to use
        c.execute("SHOW TABLES LIKE 'inventory_batches'")
        source_table = 'inventory_batches' if c.fetchone() else 'batches'
        print(f"  [INFO] Using {source_table} as pricing source.")

        c.execute(f"""
            UPDATE medicines m 
            SET selling_price = (SELECT MAX(selling_price) FROM {source_table} b WHERE b.medicine_id = m.medicine_id),
                mrp = (SELECT MAX(mrp) FROM {source_table} b WHERE b.medicine_id = m.medicine_id),
                discount_percent = (SELECT MAX(discount_percent) FROM {source_table} b WHERE b.medicine_id = m.medicine_id)
            WHERE EXISTS (SELECT 1 FROM {source_table} b WHERE b.medicine_id = m.medicine_id)
        """)

        # 3. Rename batches to inventory_batches
        print("Renaming 'batches' table to 'inventory_batches'...")
        # Check if table exists before renaming
        c.execute("SHOW TABLES LIKE 'batches'")
        if c.fetchone():
            c.execute('RENAME TABLE batches TO inventory_batches')
        else:
            print("Table 'batches' not found, skipping rename (might already be renamed).")

        # 4. Refactor inventory_batches columns
        print("Refactoring inventory_batches columns...")
        # Check if batch_no exists (to avoid error if already renamed)
        c.execute("SHOW COLUMNS FROM inventory_batches LIKE 'batch_no'")
        if c.fetchone():
            c.execute('ALTER TABLE inventory_batches CHANGE COLUMN batch_no batch_number VARCHAR(50)')
        
        add_column_if_not_exists('inventory_batches', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

        def drop_column_if_exists(table, column):
            c.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
            if c.fetchone():
                c.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
                print(f"  [OK] Dropped {column} from {table}.")
            else:
                print(f"  [INFO] {column} does not exist in {table}, skipping drop.")

        drop_column_if_exists('inventory_batches', 'mrp')
        drop_column_if_exists('inventory_batches', 'selling_price')
        drop_column_if_exists('inventory_batches', 'discount_percent')

        # 6. Add UNIQUE constraint
        print("Deduplicating and adding UNIQUE constraint...")
        # Remove duplicates before adding unique index
        c.execute("""
            DELETE i1 FROM inventory_batches i1 
            INNER JOIN inventory_batches i2 
            WHERE i1.batch_id > i2.batch_id 
              AND i1.medicine_id = i2.medicine_id 
              AND i1.batch_number = i2.batch_number
        """)
        
        # Check if index exists
        c.execute("SHOW INDEX FROM inventory_batches WHERE Key_name = 'idx_med_batch'")
        if not c.fetchone():
            c.execute('ALTER TABLE inventory_batches ADD UNIQUE INDEX idx_med_batch (medicine_id, batch_number)')

        conn.commit()
        print("\n--- Migration successfully completed! ---")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)
    finally:
        c.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
