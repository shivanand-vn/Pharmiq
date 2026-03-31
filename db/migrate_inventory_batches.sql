-- ============================================
-- Migration: Inventory Module Refactor
-- ============================================

-- 1. Update medicines table with pricing
ALTER TABLE medicines 
ADD COLUMN IF NOT EXISTS selling_price DECIMAL(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS mrp DECIMAL(10,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS discount_percent DECIMAL(5,2) DEFAULT 0.00;

-- 2. Migrate pricing from batches (latest/max) to medicines
UPDATE medicines m
SET m.selling_price = (SELECT MAX(b.selling_price) FROM batches b WHERE b.medicine_id = m.medicine_id),
    m.mrp = (SELECT MAX(b.mrp) FROM batches b WHERE b.medicine_id = m.medicine_id),
    m.discount_percent = (SELECT MAX(b.discount_percent) FROM batches b WHERE b.medicine_id = m.medicine_id);

-- 3. Rename batches to inventory_batches
-- Since inventory_batches already exists in some contexts or we want to be safe, 
-- we'll just rename it. If batches exists, rename it.
RENAME TABLE batches TO inventory_batches;

-- 4. Refactor inventory_batches columns to match new requirements
ALTER TABLE inventory_batches
CHANGE COLUMN batch_no batch_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 5. Drop redundant columns from inventory_batches
-- These are now on the medicine level
ALTER TABLE inventory_batches
DROP COLUMN IF EXISTS mrp,
DROP COLUMN IF EXISTS selling_price,
DROP COLUMN IF EXISTS discount_percent;

-- 6. Add UNIQUE constraint to prevent duplicate medicine+batch entries
-- This is critical for the new "Merge Stock" logic
ALTER TABLE inventory_batches 
ADD UNIQUE INDEX idx_med_batch (medicine_id, batch_number);
