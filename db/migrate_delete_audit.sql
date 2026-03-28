-- ============================================
-- PharmIQ — Audit Log Migration
-- Run ONCE: mysql -u root -p pharmiq < db/migrate_delete_audit.sql
-- ============================================

CREATE TABLE IF NOT EXISTS deleted_customers_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    license_no VARCHAR(50) NOT NULL,
    shop_name VARCHAR(200),
    distributor_id INT NOT NULL,
    deleted_by_user_id INT NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
