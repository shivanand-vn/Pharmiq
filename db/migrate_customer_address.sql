-- ============================================
-- PharmIQ — Customer Address Migration
-- Run ONCE: mysql -u root -p pharmiq < db/migrate_customer_address.sql
-- ============================================

-- Step 1: Add structured address columns
ALTER TABLE customers
  ADD COLUMN IF NOT EXISTS address_line1 VARCHAR(255) NOT NULL DEFAULT '' AFTER email,
  ADD COLUMN IF NOT EXISTS address_line2 VARCHAR(255) DEFAULT NULL AFTER address_line1,
  ADD COLUMN IF NOT EXISTS city VARCHAR(100) NOT NULL DEFAULT '' AFTER address_line2,
  ADD COLUMN IF NOT EXISTS dist VARCHAR(100) NOT NULL DEFAULT '' AFTER city,
  ADD COLUMN IF NOT EXISTS state VARCHAR(100) NOT NULL DEFAULT '' AFTER dist,
  ADD COLUMN IF NOT EXISTS pincode VARCHAR(10) NOT NULL DEFAULT '' AFTER state,
  ADD COLUMN IF NOT EXISTS country VARCHAR(50) NOT NULL DEFAULT 'India' AFTER pincode;

-- Step 2: Migrate existing address data into address_line1
UPDATE customers SET address_line1 = COALESCE(address, '') WHERE address IS NOT NULL AND address_line1 = '';

-- Step 3: Drop the old address column
ALTER TABLE customers DROP COLUMN IF EXISTS address;
