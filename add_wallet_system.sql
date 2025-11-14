-- Add Wallet System to Art Auction Database
-- Run this script to add wallet functionality

USE art_auction_db;

-- Add wallet_balance column to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS wallet_balance DECIMAL(10, 2) DEFAULT 0.00 AFTER password_hash;

-- Create wallet_transactions table to track all wallet activities
CREATE TABLE IF NOT EXISTS wallet_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    transaction_type ENUM('top_up', 'payment_received', 'payment_made', 'cash_out') NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    description TEXT,
    reference_id INT DEFAULT NULL,  -- auction_id for payments, NULL for top-ups/cash-outs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_transactions (user_id, created_at DESC)
);

-- Show updated users table structure
DESCRIBE users;

-- Show wallet_transactions table structure
DESCRIBE wallet_transactions;
