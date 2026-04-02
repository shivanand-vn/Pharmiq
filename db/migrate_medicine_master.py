from db.connection import get_connection
import sys

def run_migration():
    conn = get_connection()
    c = conn.cursor()
    try:
        print("Modifying medicines table to include master data fields...")
        
        def add_column_if_not_exists(table, column, definition):
            c.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
            if not c.fetchone():
                c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                print(f"  [OK] Added {column} to {table}.")
            else:
                print(f"  [INFO] {column} already exists in {table}.")

        add_column_if_not_exists('medicines', 'manufacturer', 'VARCHAR(200)')
        add_column_if_not_exists('medicines', 'category', 'VARCHAR(100)')
        add_column_if_not_exists('medicines', 'description', 'TEXT')
        
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
