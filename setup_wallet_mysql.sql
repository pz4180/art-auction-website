-- MySQL Wallet Setup Script
-- Compatible with MySQL 5.7+ and MySQL 8.0+
-- Run this script to ensure wallet system is properly configured

USE art_auction_db;

-- Step 1: Add wallet_balance column to users table (if it doesn't exist)
-- This uses a procedure to safely add the column
DELIMITER $$

DROP PROCEDURE IF EXISTS add_wallet_column$$
CREATE PROCEDURE add_wallet_column()
BEGIN
    -- Check if wallet_balance column exists
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'art_auction_db'
        AND TABLE_NAME = 'users'
        AND COLUMN_NAME = 'wallet_balance'
    ) THEN
        ALTER TABLE users ADD COLUMN wallet_balance DECIMAL(10, 2) DEFAULT 0.00 AFTER password_hash;
        SELECT 'Added wallet_balance column to users table' AS status;
    ELSE
        SELECT 'wallet_balance column already exists' AS status;
    END IF;
END$$

DELIMITER ;

CALL add_wallet_column();
DROP PROCEDURE IF EXISTS add_wallet_column;

-- Step 2: Create wallet_transactions table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS wallet_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    transaction_type ENUM('top_up', 'payment_received', 'payment_made', 'cash_out') NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    description TEXT,
    reference_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_transactions (user_id, created_at DESC)
);

-- Step 3: Verify the setup
SELECT 'Wallet system setup complete!' AS status;

-- Show wallet_balance column
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_DEFAULT,
    IS_NULLABLE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'art_auction_db'
AND TABLE_NAME = 'users'
AND COLUMN_NAME = 'wallet_balance';

-- Show wallet_transactions table exists
SELECT
    TABLE_NAME,
    TABLE_TYPE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'art_auction_db'
AND TABLE_NAME = 'wallet_transactions';

-- Count existing wallet transactions
SELECT COUNT(*) as transaction_count FROM wallet_transactions;
