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

            query = """SELECT b.*, a.title, a.image_path, a.end_time, a.status, a.payment_status,
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
                      WHERE a.winner_id = %s AND a.status IN ('completed', 'sold')
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
    
    def get_highest_bid(self, auction_id):
        """Get the highest bid for a given auction"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT b.bid_id, b.bidder_id, b.bid_amount, u.username as bidder_name
                FROM bids b
                JOIN users u ON b.bidder_id = u.user_id
                WHERE b.auction_id = %s
                ORDER BY b.bid_amount DESC
                LIMIT 1
            """
            cursor.execute(query, (auction_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error getting highest bid: {e}")
            return None
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

    def update_auction_info(self, auction_id, title, description, category_id, duration_days):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            end_time = datetime.now() + timedelta(days=duration_days)
            cur.execute("""
                UPDATE auctions
                SET title=%s, description=%s, category_id=%s, end_time=%s
                WHERE auction_id=%s
            """, (title, description, category_id, end_time, auction_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print("Error updating auction:", e)
            return False


    def delete_auction(self, auction_id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM auctions WHERE auction_id=%s", (auction_id,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print("Error deleting auction:", e)
            return False

    
    def sell_now(self, auction_id):
        """End an auction immediately and sell to the highest bidder"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            cursor = conn.cursor(dictionary=True)

            # Get highest bid
            highest_bid = self.get_highest_bid(auction_id)
            if not highest_bid:
                return False, "No bids yet — cannot sell immediately."

            bidder_id = highest_bid['bidder_id']
            bid_amount = highest_bid['bid_amount']

            # Update auction as sold
            cursor.execute("""
                UPDATE auctions
                SET status = 'sold',
                    sold_price = %s,
                    winner_id = %s,
                    end_time = NOW()
                WHERE auction_id = %s
            """, (bid_amount, bidder_id, auction_id))

            # Create notification for buyer
            message = f"Congratulations! You won auction #{auction_id} for RM{bid_amount:.2f}. Please complete your payment."
            self.create_notification(bidder_id, message, 'won')

            conn.commit()
            return True, "Auction sold immediately to highest bidder."
        
        except Error as e:
            print("❌ MySQL error in sell_now():", e)  # <-- add this
            conn.rollback()
            return False, f"MySQL error: {str(e)}"  # <-- change message to show real cause
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_pending_payments(self, user_id):
        """Get auctions won by user that require payment"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)

            query = """SELECT a.*, u.username as seller_name, c.category_name,
                      COALESCE(a.sold_price, a.current_bid) as final_price
                      FROM auctions a
                      JOIN users u ON a.seller_id = u.user_id
                      LEFT JOIN categories c ON a.category_id = c.category_id
                      WHERE a.winner_id = %s
                      AND a.status IN ('completed', 'sold')
                      AND (a.payment_status IS NULL OR a.payment_status = 'pending')
                      ORDER BY a.end_time DESC"""

            cursor.execute(query, (user_id,))
            return cursor.fetchall()

        except Error as e:
            print(f"Error getting pending payments: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def mark_payment_complete(self, auction_id, user_id):
        """Mark an auction payment as complete"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Verify the user is the winner before allowing payment
            cursor.execute("""UPDATE auctions
                            SET payment_status = 'paid'
                            WHERE auction_id = %s AND winner_id = %s""",
                          (auction_id, user_id))

            conn.commit()

            if cursor.rowcount > 0:
                # Notify seller that payment is received
                cursor.execute("SELECT seller_id, title FROM auctions WHERE auction_id = %s",
                             (auction_id,))
                auction_info = cursor.fetchone()
                if auction_info:
                    self.create_notification(
                        auction_info[0],
                        f"Payment received for '{auction_info[1]}'",
                        'won'
                    )
                return True
            return False

        except Error as e:
            print(f"Error marking payment complete: {e}")
            conn.rollback()
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
# ==================== WALLET OPERATIONS ====================

    def get_wallet_balance(self, user_id):
        """Get user's current wallet balance"""
        conn = self.get_connection()
        if not conn:
            return 0.00

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT wallet_balance FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return float(result['wallet_balance']) if result else 0.00

        except Error as e:
            print(f"Error getting wallet balance: {e}")
            return 0.00
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def add_to_wallet(self, user_id, amount, transaction_type, description, reference_id=None):
        """Add funds to user's wallet and record transaction"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor(dictionary=True)

            # Get current balance
            cursor.execute("SELECT wallet_balance FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            current_balance = float(result['wallet_balance']) if result else 0.00

            # Calculate new balance
            new_balance = current_balance + float(amount)

            # Update user's wallet balance
            cursor.execute("""UPDATE users SET wallet_balance = %s WHERE user_id = %s""",
                         (new_balance, user_id))

            # Record transaction
            cursor.execute("""
                INSERT INTO wallet_transactions
                (user_id, transaction_type, amount, balance_after, description, reference_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, transaction_type, amount, new_balance, description, reference_id))

            conn.commit()
            return True

        except Error as e:
            print(f"Error adding to wallet: {e}")
            conn.rollback()
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def deduct_from_wallet(self, user_id, amount, transaction_type, description, reference_id=None):
        """Deduct funds from user's wallet and record transaction"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            cursor = conn.cursor(dictionary=True)

            # Get current balance
            cursor.execute("SELECT wallet_balance FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            current_balance = float(result['wallet_balance']) if result else 0.00

            # Check if sufficient balance
            if current_balance < float(amount):
                return False, "Insufficient wallet balance"

            # Calculate new balance
            new_balance = current_balance - float(amount)

            # Update user's wallet balance
            cursor.execute("""UPDATE users SET wallet_balance = %s WHERE user_id = %s""",
                         (new_balance, user_id))

            # Record transaction
            cursor.execute("""
                INSERT INTO wallet_transactions
                (user_id, transaction_type, amount, balance_after, description, reference_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, transaction_type, amount, new_balance, description, reference_id))

            conn.commit()
            return True, "Success"

        except Error as e:
            print(f"Error deducting from wallet: {e}")
            conn.rollback()
            return False, str(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_wallet_transactions(self, user_id, limit=50):
        """Get user's wallet transaction history"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT * FROM wallet_transactions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (user_id, limit))
            return cursor.fetchall()

        except Error as e:
            print(f"Error getting wallet transactions: {e}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def process_wallet_payment(self, auction_id, buyer_id):
        """Process payment using wallet (buyer pays, seller receives)"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            cursor = conn.cursor(dictionary=True)

            # Get auction details
            cursor.execute("""
                SELECT seller_id, title, sold_price, current_bid, winner_id
                FROM auctions
                WHERE auction_id = %s
            """, (auction_id,))
            auction = cursor.fetchone()

            if not auction:
                return False, "Auction not found"

            if auction['winner_id'] != buyer_id:
                return False, "You are not the winner of this auction"

            seller_id = auction['seller_id']
            amount = float(auction['sold_price'] or auction['current_bid'])
            title = auction['title']

            # Get buyer's wallet balance
            cursor.execute("SELECT wallet_balance FROM users WHERE user_id = %s", (buyer_id,))
            buyer = cursor.fetchone()
            buyer_balance = float(buyer['wallet_balance']) if buyer else 0.00

            if buyer_balance < amount:
                return False, f"Insufficient wallet balance. You need {amount - buyer_balance:.2f} more."

            # Deduct from buyer
            new_buyer_balance = buyer_balance - amount
            cursor.execute("UPDATE users SET wallet_balance = %s WHERE user_id = %s",
                         (new_buyer_balance, buyer_id))

            # Add to seller
            cursor.execute("SELECT wallet_balance FROM users WHERE user_id = %s", (seller_id,))
            seller = cursor.fetchone()
            seller_balance = float(seller['wallet_balance']) if seller else 0.00
            new_seller_balance = seller_balance + amount
            cursor.execute("UPDATE users SET wallet_balance = %s WHERE user_id = %s",
                         (new_seller_balance, seller_id))

            # Record buyer transaction
            cursor.execute("""
                INSERT INTO wallet_transactions
                (user_id, transaction_type, amount, balance_after, description, reference_id)
                VALUES (%s, 'payment_made', %s, %s, %s, %s)
            """, (buyer_id, amount, new_buyer_balance, f"Payment for '{title}'", auction_id))

            # Record seller transaction
            cursor.execute("""
                INSERT INTO wallet_transactions
                (user_id, transaction_type, amount, balance_after, description, reference_id)
                VALUES (%s, 'payment_received', %s, %s, %s, %s)
            """, (seller_id, amount, new_seller_balance, f"Payment received for '{title}'", auction_id))

            # Mark auction as paid
            cursor.execute("UPDATE auctions SET payment_status = 'paid' WHERE auction_id = %s",
                         (auction_id,))

            # Notify seller
            self.create_notification(
                seller_id,
                f"Payment of RM{amount:.2f} received for '{title}' (added to wallet)",
                'won'
            )

            conn.commit()
            return True, "Payment completed successfully using wallet"

        except Error as e:
            print(f"Error processing wallet payment: {e}")
            conn.rollback()
            return False, str(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_total_earned(self, user_id):
        """Get total amount earned by seller from paid auctions"""
        conn = self.get_connection()
        if not conn:
            return 0.00

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT SUM(amount) as total_earned
                FROM wallet_transactions
                WHERE user_id = %s AND transaction_type = 'payment_received'
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return float(result['total_earned']) if result and result['total_earned'] else 0.00

        except Error as e:
            print(f"Error getting total earned: {e}")
            return 0.00
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def end_auction_immediately(self, auction_id, seller_id):
        """End an active auction immediately and sell to current highest bidder"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            cursor = conn.cursor(dictionary=True)

            # Verify the seller owns this auction and it's active
            cursor.execute("""
                SELECT auction_id, seller_id, title, status, current_bid
                FROM auctions
                WHERE auction_id = %s AND seller_id = %s
            """, (auction_id, seller_id))

            auction = cursor.fetchone()

            if not auction:
                return False, "Auction not found or you don't have permission"

            if auction['status'] != 'active':
                return False, "Auction is not active"

            # Get the current highest bidder
            cursor.execute("""
                SELECT bidder_id, bid_amount
                FROM bids
                WHERE auction_id = %s
                ORDER BY bid_amount DESC
                LIMIT 1
            """, (auction_id,))

            highest_bid = cursor.fetchone()

            if not highest_bid:
                return False, "No bids have been placed yet"

            # Update auction: set status to completed, set winner, set sold_price
            cursor.execute("""
                UPDATE auctions
                SET status = 'completed',
                    winner_id = %s,
                    sold_price = %s,
                    end_time = NOW()
                WHERE auction_id = %s
            """, (highest_bid['bidder_id'], highest_bid['bid_amount'], auction_id))

            # Notify the winner
            self.create_notification(
                highest_bid['bidder_id'],
                f"Congratulations! The seller accepted your bid for '{auction['title']}'. Please complete payment.",
                'won'
            )

            conn.commit()
            return True, "Auction ended successfully. Buyer has been notified."

        except Error as e:
            print(f"Error ending auction immediately: {e}")
            conn.rollback()
            return False, f"Database error: {str(e)}"
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

# Create a singleton instance
db_manager = DatabaseManager()