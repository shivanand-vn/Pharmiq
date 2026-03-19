-- ============================================
-- PharmIQ Seed Data for Testing
-- ============================================

-- ----------------------------
-- ROLES
-- ----------------------------
INSERT IGNORE INTO roles (role_id, role_name) VALUES
(1, 'Admin'),
(2, 'Biller'),
(3, 'Accountant');

-- ----------------------------
-- DISTRIBUTOR 1: SV Pharma
-- ----------------------------
INSERT IGNORE INTO distributors (distributor_id, name, mobile_no, email, address, gst_no, drug_license_no, logo_path, bank_name, bank_account_no, bank_ifsc, bank_branch, bank_upi, signatory_name, status)
VALUES (1, 'SV PHARMACEUTICALS', '9876543210', 'svpharma@email.com',
    '1st Floor, Trade Center, Station Road, Hubli - 580021, Karnataka',
    '29AABCS1234F1Z5', 'KA-HB-20B1/21B1-21786',
    NULL, 'HDFC BANK LTD', '99947977777777', 'HDFC0009254',
    'Deshpande Nagar Branch, Hubli', 'svpharma@upi', 'S.V. Kumar', 'active');

-- ----------------------------
-- DISTRIBUTOR 2: AR Pharma
-- ----------------------------
INSERT IGNORE INTO distributors (distributor_id, name, mobile_no, email, address, gst_no, drug_license_no, logo_path, bank_name, bank_account_no, bank_ifsc, bank_branch, bank_upi, signatory_name, status)
VALUES (2, 'AR PHARMA DISTRIBUTORS', '9988776655', 'arpharma@email.com',
    '2nd Floor, MG Road Complex, Dharwad - 580001, Karnataka',
    '29BBRCA5678G2Z8', 'KA-DW-30C1/31C1-31892',
    NULL, 'SBI', '38219876543210', 'SBIN0001234',
    'College Road Branch, Dharwad', 'arpharma@upi', 'A.R. Patil', 'active');

-- ----------------------------
-- LICENSES
-- ----------------------------
INSERT IGNORE INTO licenses (license_id, distributor_id, start_date, expiry_date, amount_paid, status)
VALUES
(1, 1, '2025-01-01', '2026-12-31', 5000.00, 'active'),
(2, 2, '2025-06-01', '2026-12-31', 5000.00, 'active');

-- ----------------------------
-- USERS (password = 'admin123' for both)
-- ----------------------------
INSERT IGNORE INTO users (user_id, distributor_id, username, password, is_first_login, status)
VALUES
(1, 1, 'svadmin', 'admin123', 0, 'active'),
(2, 1, 'svbiller', 'bill123', 0, 'active'),
(3, 2, 'aradmin', 'admin123', 0, 'active');

-- ----------------------------
-- USER_ROLES
-- ----------------------------
INSERT IGNORE INTO user_roles (user_id, role_id) VALUES
(1, 1),
(2, 2),
(3, 1);

-- ----------------------------
-- CUSTOMERS
-- ----------------------------
INSERT IGNORE INTO customers (license_no, distributor_id, shop_name, license_holder_name, mobile_no, gst_no, email, address, status)
VALUES
('REG NO KMC 118112', 1, 'ASHWINI SPECIALITY CLINIC', 'DR VIVEKAND KAMAT', '9902656680',
 '29AABCK9999E1ZP', 'ashwini@email.com',
 'C/O Ashwini Speciality Clinic, Near Ram Mandir, Thane Road, Dharwad, State: 29-Karnataka', 'active'),
('REG NO KMC 220045', 1, 'SAGAR MEDICALS', 'MR SAGAR PATIL', '9845123456',
 '29BBCDS7777F1Z3', 'sagar@email.com',
 'Shop No 5, Main Road, Hubli - 580021, Karnataka', 'active'),
('REG NO DW 330012', 2, 'PRIYA PHARMACY', 'MS PRIYA SHARMA', '9876012345',
 '29CCDEP3333G1Z1', 'priya@email.com',
 'Near Bus Stand, College Road, Dharwad - 580001, Karnataka', 'active');

-- ----------------------------
-- SUPPLIERS
-- ----------------------------
INSERT IGNORE INTO suppliers (supplier_id, distributor_id, name, mobile_no, gst_no)
VALUES
(1, 1, 'Sun Pharma Ltd', '9800011111', '27AABCS5678H1Z2'),
(2, 1, 'Cipla Ltd', '9800022222', '27AABCC9012I1Z4'),
(3, 2, 'Dr Reddys Labs', '9800033333', '36AABCD3456J1Z6');

-- ----------------------------
-- MEDICINES
-- ----------------------------
INSERT IGNORE INTO medicines (medicine_id, name, unit, gst_percent) VALUES
(1, 'GLIPY DM TAB', 'TAB', 12.00),
(2, 'AMOXICILLIN 500MG CAP', 'CAP', 12.00),
(3, 'PARACETAMOL 650MG TAB', 'TAB', 5.00),
(4, 'CETIRIZINE 10MG TAB', 'TAB', 12.00),
(5, 'PANTOPRAZOLE 40MG TAB', 'TAB', 12.00),
(6, 'AZITHROMYCIN 500MG TAB', 'TAB', 12.00),
(7, 'METFORMIN 500MG TAB', 'TAB', 5.00),
(8, 'OMEPRAZOLE 20MG CAP', 'CAP', 12.00),
(9, 'RANITIDINE 150MG TAB', 'TAB', 18.00),
(10, 'DOLO 650 TAB', 'TAB', 5.00);

-- ----------------------------
-- BATCHES (for distributor 1 - SV Pharma)
-- ----------------------------
INSERT IGNORE INTO batches (batch_id, medicine_id, supplier_id, distributor_id, batch_no, expiry_date, quantity, purchase_price, mrp)
VALUES
(1, 1, 1, 1, 'FJ49650911', '2026-09-30', 500, 220.57, 308.80),
(2, 2, 2, 1, 'AMX2024B01', '2027-03-31', 1000, 85.00, 120.50),
(3, 3, 1, 1, 'PCM650A22', '2027-06-30', 2000, 15.00, 25.00),
(4, 4, 2, 1, 'CET10B033', '2026-12-31', 800, 12.00, 22.00),
(5, 5, 1, 1, 'PAN40C044', '2027-01-31', 600, 45.00, 68.50),
(6, 6, 2, 1, 'AZI500D55', '2026-11-30', 300, 78.00, 115.00),
(7, 7, 1, 1, 'MET500E66', '2027-08-31', 1500, 8.00, 15.00),
(8, 8, 2, 1, 'OME20F077', '2026-10-31', 400, 32.00, 52.00);

-- ----------------------------
-- BATCHES (for distributor 2 - AR Pharma)
-- ----------------------------
INSERT IGNORE INTO batches (batch_id, medicine_id, supplier_id, distributor_id, batch_no, expiry_date, quantity, purchase_price, mrp)
VALUES
(9,  9, 3, 2, 'RAN150G88', '2027-04-30', 700, 18.00, 30.00),
(10, 10, 3, 2, 'DOL650H99', '2027-05-31', 900, 20.00, 35.00),
(11, 1,  3, 2, 'GLI500I10', '2026-08-31', 400, 215.00, 305.00)
