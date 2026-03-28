-- ============================================
-- PharmIQ Database Schema
-- ============================================

-- ----------------------------
-- DISTRIBUTORS (MAIN ACCOUNT)
-- ----------------------------
CREATE TABLE IF NOT EXISTS distributors (
    distributor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    mobile_no VARCHAR(15),
    email VARCHAR(100),
    address TEXT,
    gst_no VARCHAR(20),
    drug_license_no VARCHAR(50),
    logo_path VARCHAR(255),
    bank_name VARCHAR(100),
    bank_account_no VARCHAR(30),
    bank_ifsc VARCHAR(15),
    bank_branch VARCHAR(100),
    bank_upi VARCHAR(100),
    signatory_name VARCHAR(100),
    signatory_img_path VARCHAR(255),
    status ENUM('active','inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------
-- USERS
-- ----------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    distributor_id INT NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100),
    mobile_no VARCHAR(15),
    password VARCHAR(255) NOT NULL,
    temp_password VARCHAR(255),
    is_first_login TINYINT(1) DEFAULT 1,
    status ENUM('active','inactive') DEFAULT 'active',
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id)
) ENGINE=InnoDB;

-- ----------------------------
-- ROLES
-- ----------------------------
CREATE TABLE IF NOT EXISTS roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- ----------------------------
-- USER_ROLES (M:N)
-- ----------------------------
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
) ENGINE=InnoDB;

-- ----------------------------
-- CUSTOMERS (PHARMACIES)
-- ----------------------------
CREATE TABLE IF NOT EXISTS customers (
    license_no VARCHAR(50) PRIMARY KEY,
    distributor_id INT NOT NULL,
    shop_name VARCHAR(200),
    license_holder_name VARCHAR(200),
    mobile_no VARCHAR(15),
    gst_no VARCHAR(20),
    email VARCHAR(100),
    address_line1 VARCHAR(255) NOT NULL DEFAULT '',
    address_line2 VARCHAR(255) DEFAULT NULL,
    city VARCHAR(100) NOT NULL DEFAULT '',
    dist VARCHAR(100) NOT NULL DEFAULT '',
    state VARCHAR(100) NOT NULL DEFAULT '',
    pincode VARCHAR(10) NOT NULL DEFAULT '',
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    status ENUM('active','inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id)
) ENGINE=InnoDB;

-- ----------------------------
-- SUPPLIERS
-- ----------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    distributor_id INT NOT NULL,
    name VARCHAR(200),
    mobile_no VARCHAR(15),
    gst_no VARCHAR(20),
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id)
) ENGINE=InnoDB;

-- ----------------------------
-- MEDICINES
-- ----------------------------
CREATE TABLE IF NOT EXISTS medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(30),
    gst_percent DECIMAL(5,2) DEFAULT 12.00
) ENGINE=InnoDB;

-- ----------------------------
-- BATCHES
-- ----------------------------
CREATE TABLE IF NOT EXISTS batches (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    supplier_id INT NOT NULL,
    distributor_id INT NOT NULL,
    batch_no VARCHAR(50),
    expiry_date DATE,
    quantity INT DEFAULT 0,
    purchase_price DECIMAL(10,2),
    mrp DECIMAL(10,2),
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id)
) ENGINE=InnoDB;

-- ----------------------------
-- PURCHASES
-- ----------------------------
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    distributor_id INT NOT NULL,
    user_id INT NOT NULL,
    date DATE,
    total_amount DECIMAL(12,2),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

-- ----------------------------
-- PURCHASE_ITEMS
-- ----------------------------
CREATE TABLE IF NOT EXISTS purchase_items (
    purchase_item_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT NOT NULL,
    batch_id INT NOT NULL,
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id),
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
) ENGINE=InnoDB;

-- ----------------------------
-- SALES
-- ----------------------------
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    distributor_id INT NOT NULL,
    user_id INT NOT NULL,
    license_no VARCHAR(50) NOT NULL,
    date DATE,
    total_amount DECIMAL(12,2),
    gst_amount DECIMAL(10,2),
    discount DECIMAL(10,2),
    grand_total DECIMAL(12,2),
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (license_no) REFERENCES customers(license_no)
) ENGINE=InnoDB;

-- ----------------------------
-- SALE_ITEMS
-- ----------------------------
CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    batch_id INT NOT NULL,
    quantity INT,
    price DECIMAL(10,2),
    gst_percent DECIMAL(5,2),
    gst_value DECIMAL(10,2),
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
) ENGINE=InnoDB;

-- ----------------------------
-- INVOICES
-- ----------------------------
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(30) NOT NULL,
    distributor_id INT NOT NULL,
    user_id INT NOT NULL,
    customer_license_no VARCHAR(50) NOT NULL,
    invoice_date DATE NOT NULL,
    order_no VARCHAR(30),
    lr_no VARCHAR(30),
    transport VARCHAR(100),
    payment_type ENUM('Credit','Cash') DEFAULT 'Credit',
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    sgst DECIMAL(10,2) DEFAULT 0.00,
    cgst DECIMAL(10,2) DEFAULT 0.00,
    total_gst DECIMAL(10,2) DEFAULT 0.00,
    grand_total DECIMAL(12,2) DEFAULT 0.00,
    amount_in_words VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_invoice_no_dist (invoice_no, distributor_id),
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (customer_license_no) REFERENCES customers(license_no)
) ENGINE=InnoDB;

-- ----------------------------
-- INVOICE_ITEMS
-- ----------------------------
CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    batch_id INT NOT NULL,
    product_name VARCHAR(200),
    batch_no VARCHAR(50),
    expiry_date DATE,
    qty INT,
    mrp DECIMAL(10,2),
    rate DECIMAL(10,2),
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    gst_percent DECIMAL(5,2) DEFAULT 0.00,
    amount DECIMAL(12,2) DEFAULT 0.00,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
) ENGINE=InnoDB;

-- ----------------------------
-- AUDIT LOGS
-- ----------------------------
CREATE TABLE IF NOT EXISTS deleted_customers_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    license_no VARCHAR(50) NOT NULL,
    shop_name VARCHAR(200),
    distributor_id INT NOT NULL,
    deleted_by_user_id INT NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
