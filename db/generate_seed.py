import sys
import os
import random
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection

def generate_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Disable foreign key checks for a clean seed
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # 1. ROLES
        print("Seeding Roles...")
        roles = [
            (1, 'Admin'),
            (2, 'Biller'),
            (3, 'Accountant')
        ]
        cursor.executemany("INSERT IGNORE INTO roles (role_id, role_name) VALUES (%s, %s)", roles)

        # 2. DISTRIBUTORS (3 total)
        print("Seeding Distributors...")
        distributors = [
            (1, 'SV PHARMACEUTICALS', '9876543210', 'svpharma@email.com', 'Hubli, Karnataka', '29AABCS1234F1Z5', 'KA-HB-20B1/21B1-21786'),
            (2, 'APEX DRUG HOUSE', '9112233445', 'apex@email.com', 'Bangalore, Karnataka', '29BBBCS5678F1ZA', 'KA-BN-20B2/21B2-55443'),
            (3, 'MODERN PHARMA DIST', '8889990001', 'modern@email.com', 'Mangalore, Karnataka', '29CCCDS9012F1ZB', 'KA-MN-20B3/21B3-99887')
        ]
        dist_data = []
        for d in distributors:
            dist_data.append((d[0], d[1], d[2], d[3], d[4], d[5], d[6], 'HDFC BANK', '999'+str(random.randint(1000000000, 9999999999)), 'HDFC0001234', 'Main Branch', 'upi@ok', 'Distributor Head'))
            
        cursor.executemany("""
            INSERT IGNORE INTO distributors (distributor_id, name, mobile_no, email, address, gst_no, drug_license_no, bank_name, bank_account_no, bank_ifsc, bank_branch, bank_upi, signatory_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, dist_data)

        # 3. USERS
        print("Seeding Users...")
        users = [
            (1, 1, 'svadmin', 'admin123', 0),
            (2, 1, 'svbiller', 'admin123', 0),
            (3, 2, 'apexadmin', 'admin123', 0),
            (4, 3, 'modernadmin', 'admin123', 0)
        ]
        cursor.executemany("INSERT IGNORE INTO users (user_id, distributor_id, username, password, is_first_login) VALUES (%s, %s, %s, %s, %s)", users)
        
        user_roles = [(1, 1), (2, 2), (3, 1), (4, 1)]
        cursor.executemany("INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (%s, %s)", user_roles)

        # 4. CUSTOMERS (12 total, distributed)
        print("Seeding Customers...")
        shops = ["LifeCare Pharmacy", "Healthy Meds", "Wellness Drugstore", "City Pharma", "National Medicals", "The Pill Box", "Vikas Medicare", "Shanti Medical Store", "Apollo Pharmacy", "MedPlus", "Guardian Pharma", "Trust Health"]
        owners = ["Rahul Sharma", "Amit Patel", "Sanjay G", "Priya K", "Anil Deshmukh", "Sameer S", "Vijay M", "Deepak R", "Sunil B", "Karan P", "Mohan T", "Arjun L"]
        cities = ["Hubli", "Dharwad", "Bangalore", "Mysore", "Belgaum", "Mangalore"]
        
        cust_list = []
        for i in range(12):
            lic = f"KA-LIC-{10000 + i}"
            gst = f"29GSTR{20000 + i}Z1"
            dist_id = random.randint(1, 3)
            city = random.choice(cities)
            cust_list.append((lic, dist_id, shops[i], owners[i], f'90000000{i:02d}', gst, f'shop{i}@email.com', f'Street {i+1}, Main Road', 'Building 123', city, city, 'Karnataka', '58000'+str(i), 'India'))
            
        cursor.executemany("""
            INSERT IGNORE INTO customers (license_no, distributor_id, shop_name, license_holder_name, mobile_no, gst_no, email, address_line1, address_line2, city, dist, state, pincode, country)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, cust_list)

        # 5. SUPPLIERS
        print("Seeding Suppliers...")
        suppliers = ["Sun Pharma", "Cipla", "Dr. Reddy's", "Lupin", "Aurobindo", "Cadila", "Intas", "Glenmark", "Alkem", "Torrent"]
        sup_data = []
        for i, s in enumerate(suppliers):
            sup_data.append((i+1, random.randint(1, 3), s, f"98888777{i:02d}", f"27SUPP{5000+i}Z5"))
        cursor.executemany("INSERT IGNORE INTO suppliers (supplier_id, distributor_id, name, mobile_no, gst_no) VALUES (%s, %s, %s, %s, %s)", sup_data)

        # 6. MEDICINES (200 total)
        print("Seeding 200 Medicines...")
        prefixes = ["GLIPY", "AMOX", "PARA", "CETRI", "PANTO", "AZI", "METFOR", "OMEP", "RANI", "DOLO", "TELMA", "ROSU", "ATV", "GLYM", "VOGLI", "MONT", "CITI", "ORNI", "OFLO", "LEVO"]
        suffixes = [" TAB", " CAP", " SYP", " INJ", " GEL", " DROP", " SR", " FORTE", " PLUS", " DM"]
        manufacturers = ["Sun Pharma", "Cipla", "Lupin", "Abbott", "GSK", "Pfizer", "Mankind", "Alkem", "Torrent", "Intas"]
        categories = ["Antibiotics", "Painkillers", "Diabetic", "Gastro", "Cardio", "General", "Respiratory"]
        
        med_list = []
        name_check = set()
        
        while len(med_list) < 200:
            prefix = random.choice(prefixes)
            # Add some salt if we run out of unique combinations
            salt = str(random.randint(5, 500)) if len(med_list) > 100 else "" 
            suffix = random.choice(suffixes)
            full_name = f"{prefix}{salt}{suffix}"
            
            if full_name not in name_check:
                name_check.add(full_name)
                mrp = round(random.uniform(20.0, 800.0), 2)
                trp = round(mrp * random.uniform(0.7, 0.9), 2)
                gst = random.choice([5.0, 12.0, 18.0])
                med_list.append((
                    full_name, 
                    random.choice(manufacturers), 
                    random.choice(categories), 
                    f"Test description for {full_name}",
                    suffix.strip(),
                    gst,
                    mrp,
                    trp,
                    0.0
                ))

        cursor.executemany("""
            INSERT IGNORE INTO medicines (name, manufacturer, category, description, unit, gst_percent, mrp, trp, discount_percent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, med_list)

        # 7. INVENTORY BATCHES (Randomly some medicines for Distributor 1)
        print("Seeding Initial Inventory...")
        cursor.execute("SELECT medicine_id, trp FROM medicines")
        all_meds = cursor.fetchall()
        
        batch_list = []
        for med in random.sample(all_meds, 50): # 50 random medicines in stock
            qty = random.randint(100, 2000)
            batch_num = f"BAT{random.randint(10000, 99999)}"
            exp = date.today() + timedelta(days=random.randint(180, 730))
            batch_list.append((
                med[0], 
                random.randint(1, 10), 
                1, # Dist 1
                batch_num,
                exp,
                qty,
                round(float(med[1]) * 0.9, 2) # Purchase price slightly below TRP
            ))
            
        cursor.executemany("""
            INSERT IGNORE INTO inventory_batches (medicine_id, supplier_id, distributor_id, batch_number, expiry_date, quantity, purchase_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, batch_list)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("\n--- DATABASE SEEDED SUCCESSFULLY WITH 200+ MEDICINES! ---")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding data: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    generate_data()
