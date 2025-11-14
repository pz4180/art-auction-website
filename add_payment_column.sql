-- Add payment_status column to auctions table if it doesn't exist
-- Run this script to update your database for payment functionality

USE art_auction_db;

-- Add payment_status column (will skip if already exists)
ALTER TABLE auctions
ADD COLUMN IF NOT EXISTS payment_status ENUM('pending', 'paid') DEFAULT 'pending' AFTER sold_price;

-- Show the updated table structure
DESCRIBE auctions;

-- Show any won auctions that need the payment_status set
SELECT auction_id, title, status, winner_id, payment_status, sold_price, current_bid
FROM auctions
WHERE winner_id IS NOT NULL
ORDER BY end_time DESC;
