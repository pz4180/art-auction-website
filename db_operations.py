import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from config import Config

class DatabaseManager:
    """Handles all database operations for the art auction website"""
    
    def __init__(self):
        self.config = {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DATABASE,
            'port': Config.MYSQL_PORT,
            'autocommit': False
        }
    
    def get_connection(self):
        """Create and return a database connection"""
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    # User Management Functions
    def create_user(self, username, email, password):
        """Create a new user account"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            password_hash = generate_password_hash(password)
            
            query = """INSERT INTO users (username, email, password_hash) 
                      VALUES (%s, %s, %s)"""
            cursor.execute(query, (username, email, password_hash))
            conn.commit()
            return True, "User created successfully"
        
        except mysql.connector.IntegrityError as e:
            if "username" in str(e):
                return False, "Username already exists"
            elif "email" in str(e):
                return False, "Email already registered"
            return False, str(e)
        except Error as e:
            return False, str(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials for login"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s OR email = %s"
            cursor.execute(query, (username, username))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                return user
            return None
        
        except Error as e:
            print(f"Error verifying user: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user information by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT user_id, username, email, created_at FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        
        except Error as e:
            print(f"Error getting user: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    # Auction Management Functions
    def create_auction(self, seller_id, title, description, image_path, category_id, 
                      starting_bid, duration_days=7):
        """Create a new auction"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            end_time = datetime.now() + timedelta(days=duration_days)
            
            query = """INSERT INTO auctions 
                      (seller_id, title, description, image_path, category_id, 
                       starting_bid, current_bid, end_time) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            cursor.execute(query, (seller_id, title, description, image_path, 
                                  category_id, starting_bid, starting_bid, end_time))
            conn.commit()
            
            # Create notification for new auction
            self.create_notification_for_new_auction(cursor.lastrowid, title)
            
            return True, cursor.lastrowid
        
        except Error as e:
            conn.rollback()
            return False, str(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_active_auctions(self, category_id=None, min_price=None, max_price=None,
                        search_term=None, limit=20, offset=0,
                        sort_by="end_time", order="ASC"):
        """Get list of active auctions with filters"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """SELECT a.*, u.username as seller_name, c.category_name,
                      COUNT(DISTINCT b.bidder_id) as bid_count,
                      COALESCE(MAX(b.bid_amount), a.starting_bid) as current_bid
                      FROM auctions a
                      LEFT JOIN users u ON a.seller_id = u.user_id
                      LEFT JOIN categories c ON a.category_id = c.category_id
                      LEFT JOIN bids b ON a.auction_id = b.auction_id
                      WHERE a.status = 'active' AND a.end_time > NOW()"""
            
            params = []
            
            if category_id:
                query += " AND a.category_id = %s"
                params.append(category_id)
            
            if min_price:
                query += " AND COALESCE(a.current_bid, a.starting_bid) >= %s"
                params.append(min_price)
            
            if max_price:
                query += " AND COALESCE(a.current_bid, a.starting_bid) <= %s"
                params.append(max_price)
            
            if search_term:
                query += " AND (a.title LIKE %s OR a.description LIKE %s)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])
            
            query += f" GROUP BY a.auction_id ORDER BY {sort_by} {order} LIMIT %s OFFSET %s"
            params.extend([limit, offset])
  
            cursor.execute(query, params)
            return cursor.fetchall()
        
        except Error as e:
            print(f"Error getting auctions: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_auction_by_id(self, auction_id):
        """Get detailed information about a specific auction"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """SELECT a.*, u.username as seller_name, c.category_name,
                      COUNT(DISTINCT b.bidder_id) as bid_count,
                      COALESCE(MAX(b.bid_amount), a.starting_bid) as current_bid
                      FROM auctions a
                      LEFT JOIN users u ON a.seller_id = u.user_id
                      LEFT JOIN categories c ON a.category_id = c.category_id
                      LEFT JOIN bids b ON a.auction_id = b.auction_id
                      WHERE a.auction_id = %s
                      GROUP BY a.auction_id"""
            
            cursor.execute(query, (auction_id,))
            auction = cursor.fetchone()
            
            if auction:
                # Get bid history
                cursor.execute("""SELECT b.*, u.username as bidder_name 
                                FROM bids b
                                JOIN users u ON b.bidder_id = u.user_id
                                WHERE b.auction_id = %s
                                ORDER BY b.bid_time DESC
                                LIMIT 10""", (auction_id,))
                auction['bid_history'] = cursor.fetchall()
            
            return auction
        
        except Error as e:
            print(f"Error getting auction: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    # Bidding Functions
    def place_bid(self, auction_id, bidder_id, bid_amount):
        """Place a bid on an auction"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if auction is still active
            cursor.execute("""SELECT * FROM auctions 
                            WHERE auction_id = %s AND status = 'active' 
                            AND end_time > NOW()""", (auction_id,))
            auction = cursor.fetchone()
            
            if not auction:
                return False, "Auction is not active or has ended"
            
            # Check if bidder is not the seller
            if auction['seller_id'] == bidder_id:
                return False, "You cannot bid on your own auction"
            
            # Get current highest bid
            current_bid = auction['current_bid'] or auction['starting_bid']
            
            # Check if bid is high enough
            min_bid = current_bid + Config.MINIMUM_BID_INCREMENT
            if bid_amount < min_bid:
                return False, f"Bid must be at least ${min_bid:.2f}"
            
            # Get previous highest bidder
            cursor.execute("""SELECT bidder_id FROM bids 
                            WHERE auction_id = %s 
                            ORDER BY bid_amount DESC LIMIT 1""", (auction_id,))
            previous_bidder = cursor.fetchone()
            
            # Insert new bid
            cursor.execute("""INSERT INTO bids (auction_id, bidder_id, bid_amount) 
                            VALUES (%s, %s, %s)""", 
                          (auction_id, bidder_id, bid_amount))
            
            # Update auction current bid
            cursor.execute("""UPDATE auctions SET current_bid = %s 
                            WHERE auction_id = %s""", 
                          (bid_amount, auction_id))
            
            # Create outbid notification for previous bidder
            if previous_bidder and previous_bidder['bidder_id'] != bidder_id:
                self.create_notification(
                    previous_bidder['bidder_id'],
                    f"You have been outbid on '{auction['title']}'",
                    'outbid'
                )
            
            conn.commit()
            return True, "Bid placed successfully"
        
        except Error as e:
            conn.rollback()
            return False, str(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_user_bids(self, user_id):
        """Get all bids placed by a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """SELECT b.*, a.title, a.image_path, a.end_time, a.status,
                      MAX(b2.bid_amount) as current_highest_bid,
                      CASE WHEN MAX(b2.bid_amount) = b.bid_amount THEN 1 ELSE 0 END as is_winning
                      FROM bids b
                      JOIN auctions a ON b.auction_id = a.auction_id
                      LEFT JOIN bids b2 ON b.auction_id = b2.auction_id
                      WHERE b.bidder_id = %s
                      GROUP BY b.bid_id
                      ORDER BY b.bid_time DESC"""
            
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        
        except Error as e:
            print(f"Error getting user bids: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    # Auction History and Results
    def get_user_auctions(self, user_id):
        """Get all auctions created by a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """SELECT a.*, c.category_name,
                      COUNT(DISTINCT b.bidder_id) as bid_count,
                      COALESCE(MAX(b.bid_amount), a.starting_bid) as final_bid,
                      w.username as winner_name
                      FROM auctions a
                      LEFT JOIN categories c ON a.category_id = c.category_id
                      LEFT JOIN bids b ON a.auction_id = b.auction_id
                      LEFT JOIN users w ON a.winner_id = w.user_id
                      WHERE a.seller_id = %s
                      GROUP BY a.auction_id
                      ORDER BY a.created_at DESC"""
            
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        
        except Error as e:
            print(f"Error getting user auctions: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_won_auctions(self, user_id):
        """Get auctions won by a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """SELECT a.*, u.username as seller_name, c.category_name
                      FROM auctions a
                      JOIN users u ON a.seller_id = u.user_id
                      LEFT JOIN categories c ON a.category_id = c.category_id
                      WHERE a.winner_id = %s AND a.status = 'completed'
                      ORDER BY a.end_time DESC"""
            
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        
        except Error as e:
            print(f"Error getting won auctions: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    # Notification Functions
    def create_notification(self, user_id, message, notification_type='new_auction'):
        """Create a notification for a user"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            query = """INSERT INTO notifications (user_id, message, type) 
                      VALUES (%s, %s, %s)"""
            cursor.execute(query, (user_id, message, notification_type))
            conn.commit()
            return True
        
        except Error as e:
            print(f"Error creating notification: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_user_notifications(self, user_id, unread_only=False):
        """Get notifications for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM notifications WHERE user_id = %s"
            if unread_only:
                query += " AND is_read = FALSE"
            query += " ORDER BY created_at DESC LIMIT 20"
            
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        
        except Error as e:
            print(f"Error getting notifications: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def mark_notifications_read(self, user_id):
        """Mark all notifications as read for a user"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            query = "UPDATE notifications SET is_read = TRUE WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            conn.commit()
            return True
        
        except Error as e:
            print(f"Error marking notifications: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def create_notification_for_new_auction(self, auction_id, title):
        """Create notifications for all users about a new auction"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Get all users except the seller
            cursor.execute("""SELECT user_id FROM users 
                            WHERE user_id != (SELECT seller_id FROM auctions 
                                             WHERE auction_id = %s)""", (auction_id,))
            users = cursor.fetchall()
            
            message = f"New auction available: '{title}'"
            
            for user in users:
                cursor.execute("""INSERT INTO notifications (user_id, message, type) 
                                VALUES (%s, %s, 'new_auction')""", 
                              (user[0], message))
            
            conn.commit()
            return True
        
        except Error as e:
            print(f"Error creating notifications: {e}")
            conn.rollback()
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def close_expired_auctions(self):
        """Close auctions that have ended and declare winners"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get expired active auctions
            cursor.execute("""SELECT a.*, MAX(b.bid_amount) as winning_bid, 
                            b.bidder_id as winner
                            FROM auctions a
                            LEFT JOIN bids b ON a.auction_id = b.auction_id
                            WHERE a.status = 'active' AND a.end_time <= NOW()
                            GROUP BY a.auction_id""")
            
            expired_auctions = cursor.fetchall()
            
            for auction in expired_auctions:
                # Update auction status and winner
                if auction['winner']:
                    cursor.execute("""UPDATE auctions 
                                    SET status = 'completed', winner_id = %s 
                                    WHERE auction_id = %s""",
                                  (auction['winner'], auction['auction_id']))
                    
                    # Notify winner
                    self.create_notification(
                        auction['winner'],
                        f"Congratulations! You won the auction for '{auction['title']}'",
                        'won'
                    )
                else:
                    cursor.execute("""UPDATE auctions SET status = 'completed' 
                                    WHERE auction_id = %s""", (auction['auction_id'],))
            
            conn.commit()
            return True
        
        except Error as e:
            print(f"Error closing auctions: {e}")
            conn.rollback()
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_categories(self):
        """Get all auction categories"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM categories ORDER BY category_name")
            return cursor.fetchall()
        
        except Error as e:
            print(f"Error getting categories: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

# Create a singleton instance
db_manager = DatabaseManager()
