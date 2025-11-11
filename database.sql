-- Art Auction Website Database Schema
-- Run this SQL script in MySQL to create the database and tables

CREATE DATABASE IF NOT EXISTS art_auction_db;
USE art_auction_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Artwork categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

-- Insert default categories
INSERT INTO categories (category_name) VALUES 
('Paintings'), ('Sculptures'), ('Photography'), 
('Digital Art'), ('Mixed Media'), ('Other');

-- Auctions table
CREATE TABLE IF NOT EXISTS auctions (
    auction_id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    image_path VARCHAR(500),
    category_id INT,
    starting_bid DECIMAL(10, 2) NOT NULL,
    current_bid DECIMAL(10, 2),
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NOT NULL,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    winner_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (winner_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_end_time (end_time)
);

-- Bids table
CREATE TABLE IF NOT EXISTS bids (
    bid_id INT AUTO_INCREMENT PRIMARY KEY,
    auction_id INT NOT NULL,
    bidder_id INT NOT NULL,
    bid_amount DECIMAL(10, 2) NOT NULL,
    bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id) ON DELETE CASCADE,
    FOREIGN KEY (bidder_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_auction (auction_id),
    INDEX idx_bidder (bidder_id)
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    type ENUM('outbid', 'won', 'new_auction', 'auction_ending') DEFAULT 'new_auction',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_read (user_id, is_read)
);

-- Watchlist table (for users to follow auctions)
CREATE TABLE IF NOT EXISTS watchlist (
    watchlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    auction_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_auction (user_id, auction_id)
);

-- Create view for active auctions with current bid info
CREATE VIEW active_auctions_view AS
SELECT 
    a.*, 
    u.username as seller_name,
    c.category_name,
    COUNT(DISTINCT b.bidder_id) as bid_count,
    MAX(b.bid_amount) as highest_bid
FROM auctions a
LEFT JOIN users u ON a.seller_id = u.user_id
LEFT JOIN categories c ON a.category_id = c.category_id
LEFT JOIN bids b ON a.auction_id = b.auction_id
WHERE a.status = 'active' AND a.end_time > NOW()
GROUP BY a.auction_id;

ALTER TABLE auctions ADD COLUMN sold_price DECIMAL(10,2) NULL AFTER current_bid;