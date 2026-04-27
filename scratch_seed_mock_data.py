import sys
import os
sys.path.append(r'f:\Pharmiq')

from db.connection import execute_query, fetch_all
from datetime import datetime, timedelta

def insert_mock_data():
    # Insert a medicine
    medicine_query = """
    INSERT INTO medicines (name, manufacturer, category, description, unit, gst_percent, mrp, trp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    execute_query(medicine_query, ("Low Stock Med", "PharmaInc", "Painkillers", "Mock Med", "Unit", 12.0, 100.0, 80.0))
    execute_query(medicine_query, ("Expiring Med", "PharmaInc", "Antibiotics", "Mock Med", "Unit", 12.0, 200.0, 150.0))
    
    medicines = fetch_all("SELECT medicine_id, name FROM medicines ORDER BY medicine_id DESC LIMIT 2")
    
    # We need a supplier
    supplier = fetch_all("SELECT supplier_id FROM suppliers LIMIT 1")
    supplier_id = supplier[0]['supplier_id'] if supplier else 1
    
    med_low_stock = next(m['medicine_id'] for m in medicines if m['name'] == 'Low Stock Med')
    med_expiring = next(m['medicine_id'] for m in medicines if m['name'] == 'Expiring Med')
    
    batch_query = """
    INSERT INTO inventory_batches (medicine_id, supplier_id, distributor_id, batch_number, expiry_date, quantity, purchase_price)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    # Distributor ID is 1
    distributor_id = 1
    
    # Low stock batch: qty < 50
    execute_query(batch_query, (med_low_stock, supplier_id, distributor_id, "BATCH_LOW_123", (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"), 15, 80.0))
    # Expiring batch: qty > 0, expiry within 90 days
    execute_query(batch_query, (med_expiring, supplier_id, distributor_id, "BATCH_EXP_456", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"), 100, 150.0))

if __name__ == "__main__":
    insert_mock_data()
    print("Mock data added.")
