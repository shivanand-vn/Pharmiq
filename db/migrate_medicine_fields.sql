-- ============================================
-- Migration: Add Medicine Pricing Fields
-- ============================================

ALTER TABLE batches 
ADD COLUMN IF NOT EXISTS selling_price DECIMAL(10,2) AFTER mrp,
ADD COLUMN IF NOT EXISTS discount_percent DECIMAL(5,2) DEFAULT 0.00 AFTER selling_price;

-- Initialize selling_price with mrp for existing records
UPDATE batches SET selling_price = mrp WHERE selling_price IS NULL;
