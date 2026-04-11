-- ============================================
-- PharmIQ Seed Data (Aligned with New Schema)
-- ============================================

-- 1. ROLES
INSERT IGNORE INTO roles (role_id, role_name) VALUES
(1, 'Admin'),
(2, 'Biller'),
(3, 'Accountant');

-- 2. DISTRIBUTORS
INSERT IGNORE INTO distributors (distributor_id, name, mobile_no, email, address, gst_no, drug_license_no, bank_name, bank_account_no, bank_ifsc, bank_branch, bank_upi, signatory_name)
VALUES 
(1, 'SV PHARMACEUTICALS', '9876543210', 'svpharma@email.com', 'Hubli, Karnataka', '29AABCS1234F1Z5', 'KA-HB-20B1/21B1-21786', 'HDFC BANK', '99947977777777', 'HDFC0009254', 'Deshpande Nagar', 'svpharma@upi', 'S.V. Kumar'),
(2, 'APEX DRUG HOUSE', '9112233445', 'apex@email.com', 'Bangalore, Karnataka', '29BBBCS5678F1ZA', 'KA-BN-20B2/21B2-55443', 'ICICI BANK', '888123456789', 'ICIC0001234', 'MG Road', 'apex@upi', 'A.P. Singh');

-- 3. USERS (password = 'admin123')
INSERT IGNORE INTO users (user_id, distributor_id, username, password, is_first_login, status)
VALUES
(1, 1, 'svadmin', 'admin123', 0, 'active'),
(2, 1, 'svbiller', 'admin123', 0, 'active'),
(3, 2, 'apexadmin', 'admin123', 0, 'active');

INSERT IGNORE INTO user_roles (user_id, role_id) VALUES
(1, 1), (2, 2), (3, 1);

-- 4. SUPPLIERS
INSERT IGNORE INTO suppliers (supplier_id, distributor_id, name, mobile_no, gst_no)
VALUES
(1, 1, 'Sun Pharma Ltd', '9800011111', '27AABCS5678H1Z2'),
(2, 1, 'Cipla Ltd', '9800022222', '27AABCC9012I1Z4');

-- 5. SAMPLE MEDICINES
-- (Run generate_seed.py for full 200+ medicines)
INSERT IGNORE INTO medicines (medicine_id, name, manufacturer, category, unit, gst_percent, mrp, trp)
VALUES
(1, 'GLIPY DM TAB', 'Sanofi', 'Diabetic', 'TAB', 12.00, 308.80, 220.57),
(2, 'AMOXICILLIN 500MG CAP', 'Cipla', 'Antibiotics', 'CAP', 12.00, 120.50, 85.00),
(3, 'PARACETAMOL 650MG TAB', 'Dolo', 'Painkillers', 'TAB', 5.00, 25.00, 15.00),
(4, 'CETIRIZINE 10MG TAB', 'Sun Pharma', 'General', 'TAB', 12.00, 22.00, 12.00),
(5, 'PANTOPRAZOLE 40MG TAB', 'Alkem', 'Gastro', 'TAB', 12.00, 68.50, 45.00);

-- 6. SAMPLE CUSTOMERS
INSERT IGNORE INTO customers (license_no, distributor_id, shop_name, license_holder_name, mobile_no, gst_no, email, address_line1, city, dist, state, pincode)
VALUES
('KA-BG3-283577', 1, 'ASHWINI SPECIALITY CLINIC', 'DR VIVEKAND KAMAT', '9902656680', '29AABCK9999E1ZP', 'ashwini@email.com', 'Near Ram Mandir', 'Dharwad', 'Dharwad', 'Karnataka', '580001'),
('KA-BG3-283578', 1, 'SAGAR MEDICALS', 'MR SAGAR PATIL', '9845123456', '29BBCDS7777F1Z3', 'sagar@email.com', 'Shop No 5, Main Road', 'Hubli', 'Dharwad', 'Karnataka', '580021');

-- 7. INITIAL STOCK
INSERT IGNORE INTO inventory_batches (medicine_id, supplier_id, distributor_id, batch_number, expiry_date, quantity, purchase_price)
VALUES
(1, 1, 1, 'FJ49650911', '2026-09-30', 500, 198.50),
(2, 2, 1, 'AMX2024B01', '2027-03-31', 1000, 75.00),
(3, 1, 1, 'PCM650A22', '2027-06-30', 2000, 12.00);
