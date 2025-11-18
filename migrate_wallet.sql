-- Simple Wallet Migration Script

USE art_auction_db;

-- Step 1: Add wallet_balance column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_balance DECIMAL(10, 2) DEFAULT 0.00 AFTER password_hash;

-- Step 2: Create wallet_transactions table
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

-- Verify the changes
SELECT 'Wallet system tables created successfully!' AS status;
SHOW COLUMNS FROM users LIKE 'wallet_balance';
SHOW TABLES LIKE 'wallet_transactions';