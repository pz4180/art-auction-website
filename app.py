from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import os
import json
import imghdr
from PIL import Image
from config import Config
from db_operations import db_manager
from decimal import Decimal

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['user_id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.created_at = user_data.get('created_at')

@login_manager.user_loader
def load_user(user_id):
    user_data = db_manager.get_user_by_id(int(user_id))
    if user_data:
        return User(user_data)
    return None

# Context processor to make wallet balance available to all templates
@app.context_processor
def inject_wallet_balance():
    if current_user.is_authenticated:
        wallet_balance = db_manager.get_wallet_balance(current_user.id)
        return dict(user_wallet_balance=wallet_balance)
    return dict(user_wallet_balance=0.00)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Helper function to resize and save images
def save_artwork_image(file):
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)

            img = Image.open(file)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(filepath, 'JPEG', quality=85, optimize=True)
            return filename
        except Exception:
            return None
    return None


# Routes
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # You can handle form submissions here, e.g. send an email or save to DB
        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route('/')
def index():
    """Home page showing featured auctions"""
    # Get random auctions for featured section
    auctions = db_manager.get_active_auctions(limit=6, random_order=True)
    # Get random auctions for hero slider (5 slides)
    slider_auctions = db_manager.get_active_auctions(limit=5, random_order=True)
    if current_user.is_authenticated:
        notifications = db_manager.get_user_notifications(current_user.id, unread_only=True)
    else:
        notifications = []
    return render_template('index.html', auctions=auctions, slider_auctions=slider_auctions, notifications=notifications)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
        else:
            success, message = db_manager.create_user(username, email, password)
            if success:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user_data = db_manager.verify_user(username, password)
        if user_data:
            user = User(user_data)
            login_user(user, remember=remember)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their auctions, bids, and notifications"""
    # Get user's auctions
    my_auctions = db_manager.get_user_auctions(current_user.id)
    
    # Get user's bids
    my_bids = db_manager.get_user_bids(current_user.id)

    # Get won auctions
    won_auctions = db_manager.get_won_auctions(current_user.id)

    # Get notifications
    notifications = db_manager.get_user_notifications(current_user.id)

    # Get pending payments count
    pending_payments = db_manager.get_pending_payments(current_user.id)
    pending_payments_count = len(pending_payments)

    # Mark notifications as read
    db_manager.mark_notifications_read(current_user.id)

    return render_template('dashboard.html',
                         my_auctions=my_auctions,
                         my_bids=my_bids,
                         won_auctions=won_auctions,
                         notifications=notifications,
                         pending_payments_count=pending_payments_count)


@app.route('/create_auction', methods=['GET', 'POST'])
@login_required
def create_auction():
    """Create new auction page"""
    categories = db_manager.get_categories()
    image_error = None  # <--- added

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        starting_bid = request.form.get('starting_bid')
        duration_days = request.form.get('duration_days', Config.DEFAULT_AUCTION_DURATION_DAYS)
        
        # Validate inputs
        if not all([title, description, starting_bid]):
            flash('Please fill in all required fields', 'danger')
        elif 'artwork_image' not in request.files:
            flash('Please upload an artwork image', 'danger')
        else:
            file = request.files['artwork_image']
            if file.filename == '':
                flash('Please select an image file', 'danger')
            elif file and allowed_file(file.filename):
                # Save image
                filename = save_artwork_image(file)
                if filename:
                    # Create auction
                    success, result = db_manager.create_auction(
                        seller_id=current_user.id,
                        title=title,
                        description=description,
                        image_path=filename,
                        category_id=int(category_id) if category_id else None,
                        starting_bid=float(starting_bid),
                        duration_days=int(duration_days)
                    )
                    
                    if success:
                        flash('Auction created successfully!', 'success')
                        return redirect(url_for('auction_detail', auction_id=result))
                    else:
                        flash(f'Error creating auction: {result}', 'danger')
                else:
                    flash('❌ Unsupported image format. Please upload a JPG, PNG, or GIF.', 'danger')
            else:
                flash('Invalid file type. Please upload an image.', 'danger')
    
    return render_template('create_auction.html', categories=categories)

# ===============================
# 🔧 Edit Auction
# ===============================
@app.route('/edit_auction/<int:auction_id>', methods=['GET', 'POST'])
@login_required
def edit_auction(auction_id):
    """Allow user to edit their auction details"""
    auction = db_manager.get_auction_by_id(auction_id)

    if not auction:
        flash('Auction not found', 'danger')
        return redirect(url_for('dashboard'))

    if auction['seller_id'] != current_user.id:
        flash('You are not authorized to edit this auction.', 'danger')
        return redirect(url_for('dashboard'))

    categories = db_manager.get_categories()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        duration_days = request.form.get('duration_days', type=int)

        if not title or not description:
            flash('Title and description are required.', 'danger')
        else:
            success = db_manager.update_auction_info(
                auction_id=auction_id,
                title=title,
                description=description,
                category_id=category_id,
                duration_days=duration_days
            )
            if success:
                flash('Auction updated successfully!', 'success')
                return redirect(url_for('auction_detail', auction_id=auction_id))
            else:
                flash('Failed to update auction.', 'danger')

    return render_template('edit_auction.html', auction=auction, categories=categories)


# ===============================
# 🗑️ Delete Auction
# ===============================
@app.route('/delete_auction/<int:auction_id>', methods=['POST'])
@login_required
def delete_auction(auction_id):
    """Allow user to delete their auction"""
    auction = db_manager.get_auction_by_id(auction_id)

    if not auction:
        flash('Auction not found', 'danger')
    elif auction['seller_id'] != current_user.id:
        flash('Unauthorized action.', 'danger')
    else:
        success = db_manager.delete_auction(auction_id)
        if success:
            flash('Auction deleted successfully.', 'success')
        else:
            flash('Failed to delete auction.', 'danger')

    return redirect(url_for('dashboard'))


# ===============================
# 💰 Sell Immediately
# ===============================
@app.route('/sell_now/<int:auction_id>', methods=['POST'])
@login_required
def sell_now(auction_id):
    """Let seller end auction early and sell to current highest bidder"""
    auction = db_manager.get_auction_by_id(auction_id)

    if not auction:
        flash('Auction not found.', 'danger')
        return redirect(url_for('dashboard'))

    if auction['seller_id'] != current_user.id:
        flash('You are not authorized to perform this action.', 'danger')
        return redirect(url_for('dashboard'))

    highest_bid = db_manager.get_highest_bid(auction_id)
    if not highest_bid:
        flash("Cannot sell immediately — no bids have been placed yet.", "warning")
        return redirect(url_for('auction_detail', auction_id=auction_id))

    success, message = db_manager.sell_now(auction_id)
    if success:
        # Notify winner
        db_manager.create_notification(
            user_id=highest_bid['bidder_id'],
            message=f"You won '{auction['title']}'!"
        )
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('dashboard'))


@app.route('/payment')
@login_required
def payment_center():
    """Payment center showing items that need payment"""
    # Get pending payments
    pending_payments = db_manager.get_pending_payments(current_user.id)

    # Get completed payments (won auctions that are paid)
    conn = db_manager.get_connection()
    completed_payments = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """SELECT a.*, u.username as seller_name, c.category_name,
                      COALESCE(a.sold_price, a.current_bid) as final_price
                      FROM auctions a
                      JOIN users u ON a.seller_id = u.user_id
                      LEFT JOIN categories c ON a.category_id = c.category_id
                      WHERE a.winner_id = %s
                      AND a.status IN ('completed', 'sold')
                      AND a.payment_status = 'paid'
                      ORDER BY a.end_time DESC
                      LIMIT 10"""
            cursor.execute(query, (current_user.id,))
            completed_payments = cursor.fetchall()
        except Exception as e:
            print(f"Error getting completed payments: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('payment.html',
                         pending_payments=pending_payments,
                         completed_payments=completed_payments)

@app.route('/payment/<int:auction_id>')
@login_required
def payment_detail(auction_id):
    """Show payment detail page for a specific auction"""
    auction = db_manager.get_auction_by_id(auction_id)

    if not auction:
        flash('Auction not found', 'danger')
        return redirect(url_for('payment_center'))

    # Verify the user is the winner
    if auction['winner_id'] != current_user.id:
        flash('You are not authorized to make payment for this auction', 'danger')
        return redirect(url_for('dashboard'))

    # Check if already paid
    if auction.get('payment_status') == 'paid':
        flash('Payment has already been completed for this auction', 'info')
        return redirect(url_for('payment_center'))

    # Add final_price field
    auction['final_price'] = auction.get('sold_price') or auction.get('current_bid')

    # Get user's wallet balance
    raw_balance = db_manager.get_wallet_balance(current_user.id)
    wallet_balance = Decimal(str(raw_balance))

    return render_template('payment_detail.html', auction=auction, wallet_balance=wallet_balance)

@app.route('/payment/<int:auction_id>/process', methods=['POST'])
@login_required
def process_payment(auction_id):
    """Process payment for an auction"""
    auction = db_manager.get_auction_by_id(auction_id)

    if not auction:
        flash('Auction not found', 'danger')
        return redirect(url_for('payment_center'))

    # Verify the user is the winner
    if auction['winner_id'] != current_user.id:
        flash('You are not authorized to make payment for this auction', 'danger')
        return redirect(url_for('dashboard'))

    payment_method = request.form.get('payment_method', 'credit_card')

    # Handle wallet payment
    if payment_method == 'wallet':
        success, message = db_manager.process_wallet_payment(auction_id, current_user.id)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    else:
        # Handle other payment methods (credit card, PayPal, etc.)
        # In real application, this would integrate with payment gateway
        # For demo, we'll just mark the payment as complete
        success = db_manager.mark_payment_complete(auction_id, current_user.id)

        if success:
            flash(f'Payment completed successfully! Thank you for your purchase.', 'success')
        else:
            flash('There was an error processing your payment. Please try again.', 'danger')

    return redirect(url_for('payment_center'))

@app.route('/wallet')
@login_required
def wallet():
    """Wallet page showing balance, transactions, and top-up/cash-out options"""
    wallet_balance = db_manager.get_wallet_balance(current_user.id)
    transactions = db_manager.get_wallet_transactions(current_user.id, limit=50)

    return render_template('wallet.html',
                         wallet_balance=wallet_balance,
                         transactions=transactions)

@app.route('/wallet/topup', methods=['POST'])
@login_required
def wallet_topup():
    """Process wallet top-up"""
    try:
        amount = request.form.get('amount', type=float)
        payment_method = request.form.get('payment_method', 'card')

        if not amount or amount < 10:
            flash('Minimum top-up amount is RM10.00', 'danger')
            return redirect(url_for('wallet'))

        if amount > 1000000:
            flash('Maximum top-up amount is RM1,000,000.00', 'danger')
            return redirect(url_for('wallet'))

        # In real application, this would integrate with payment gateway
        # For demo, we'll add funds immediately
        success = db_manager.add_to_wallet(
            current_user.id,
            amount,
            'top_up',
            f'Wallet top-up via {payment_method}'
        )

        if success:
            flash(f'Successfully added RM{amount:.2f} to your wallet!', 'success')
        else:
            flash('Failed to top-up wallet. Please run database migration: mysql -u root -p art_auction_db < add_wallet_system.sql', 'danger')

    except Exception as e:
        print(f"Error in wallet_topup: {e}")
        flash(f'Database error: {str(e)}. Please ensure wallet tables exist by running: add_wallet_system.sql', 'danger')

    return redirect(url_for('wallet'))

@app.route('/wallet/cashout', methods=['POST'])
@login_required
def wallet_cashout():
    """Process wallet cash-out"""
    amount = request.form.get('amount', type=float)
    bank_account = request.form.get('bank_account', '')
    bank_name = request.form.get('bank_name', '')

    if not amount or amount < 10:
        flash('Minimum cash-out amount is RM10.00', 'danger')
        return redirect(url_for('wallet'))

    if not bank_account or not bank_name:
        flash('Please provide bank account details', 'danger')
        return redirect(url_for('wallet'))

    # Check if user has sufficient balance
    current_balance = db_manager.get_wallet_balance(current_user.id)
    if current_balance < amount:
        flash('Insufficient wallet balance', 'danger')
        return redirect(url_for('wallet'))

    # Deduct from wallet
    success, message = db_manager.deduct_from_wallet(
        current_user.id,
        amount,
        'cash_out',
        f'Cash out to {bank_name} account {bank_account[-4:]}'
    )

    if success:
        flash(f'Cash out request for RM{amount:.2f} submitted successfully! Funds will be transferred to your {bank_name} account within 1-3 business days.', 'success')
    else:
        flash(f'Failed to process cash-out: {message}', 'danger')

    return redirect(url_for('wallet'))

@app.route('/browse')
def browse_auctions():
    """Browse all active auctions with search and filter"""
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search_term = request.args.get('search', '')
    sort = request.args.get('sort', 'ending_soon')  
    page = request.args.get('page', 1, type=int)
    
    # Pagination
    per_page = 12
    offset = (page - 1) * per_page
    
    sort_by = None
    order = "ASC"

    if sort == "ending_soon":
        sort_by = "end_time"
        order = "ASC"
    elif sort == "newly_listed":
        sort_by = "created_at"
        order = "DESC"
    elif sort == "price_low":
        sort_by = "current_bid"
        order = "ASC"
    elif sort == "price_high":
        sort_by = "current_bid"
        order = "DESC"
    elif sort == "most_bids":
        sort_by = "bid_count"
        order = "DESC"

    # Get auctions
    auctions = db_manager.get_active_auctions(
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search_term=search_term if search_term else None,
        limit=per_page,
        offset=offset,
        sort_by=sort_by,
        order=order
    )
    
    # Get categories for filter
    categories = db_manager.get_categories()
    
    return render_template(
        'browse_auctions.html',
        auctions=auctions,
        categories=categories,
        current_category=category_id,
        search_term=search_term,
        min_price=min_price,
        max_price=max_price,
        page=page,
        sort=sort  # ✅ Pass it back to template
    )

@app.route('/auction/<int:auction_id>')
def auction_detail(auction_id):
    """View detailed auction page"""
    auction = db_manager.get_auction_by_id(auction_id)
    
    if not auction:
        flash('Auction not found', 'warning')
        return redirect(url_for('browse_auctions'))
    
    # Check if auction has ended
    auction['has_ended'] = datetime.now() > auction['end_time']
    auction['time_remaining'] = auction['end_time'] - datetime.now()
    
    # Check if current user is winning
    if current_user.is_authenticated and auction.get('bid_history'):
        auction['user_is_winning'] = auction['bid_history'][0]['bidder_id'] == current_user.id
    else:
        auction['user_is_winning'] = False
    
    return render_template('auction_detail.html', auction=auction)

@app.route('/place_bid/<int:auction_id>', methods=['POST'])
@login_required
def place_bid(auction_id):
    """Place a bid on an auction"""
    bid_amount = request.form.get('bid_amount', type=float)
    
    if not bid_amount:
        flash('Please enter a bid amount', 'danger')
    else:
        success, message = db_manager.place_bid(auction_id, current_user.id, bid_amount)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    
    return redirect(url_for('auction_detail', auction_id=auction_id))

@app.route('/auction_history')
@login_required
def auction_history():
    """View user's auction history"""
    # Get user's past auctions (as seller)
    my_past_auctions = db_manager.get_user_auctions(current_user.id)
    
    
    # Get user's bidding history
    my_bid_history = db_manager.get_user_bids(current_user.id)

    # Get won auctions
    won_auctions = db_manager.get_won_auctions(current_user.id)

        # Calculate total spent (float)
    total_spent_raw = sum(
        (auction.get('sold_price') or auction.get('current_bid') or 0)
        for auction in won_auctions
        if auction.get('payment_status') == 'paid'
    )

    # Convert to Decimal
    total_spent = Decimal(str(total_spent_raw))

    # Get total earned (as seller from paid auctions)
    try:
        total_earned = db_manager.get_total_earned(current_user.id)
        total_earned = Decimal(str(total_earned))  # ensure Decimal
    except Exception as e:
        print(f"Error getting total earned: {e}")
        total_earned = Decimal("0.00")

    return render_template('auction_history.html',
                         my_past_auctions=my_past_auctions,
                         my_bid_history=my_bid_history,
                         won_auctions=won_auctions,
                         total_spent=total_spent,
                         total_earned=total_earned)

@app.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint to get user notifications"""
    limit = request.args.get('limit', 20, type=int)

    # Get all notifications (read and unread) with limit
    all_notifications = db_manager.get_user_notifications(current_user.id, unread_only=False, limit=limit)

    # Get count of unread notifications
    unread_notifications = db_manager.get_user_notifications(current_user.id, unread_only=True)

    return jsonify({
        'count': len(all_notifications),
        'unread_count': len(unread_notifications),
        'notifications': all_notifications
    })

@app.route('/api/mark_notifications_read', methods=['POST'])
@login_required
def mark_notifications_read():
    """API endpoint to mark notifications as read"""
    success = db_manager.mark_notifications_read(current_user.id)
    return jsonify({'success': success})

@app.route('/api/check_auction_status')
def check_auction_status():
    """API endpoint to check and update auction statuses"""
    db_manager.close_expired_auctions()
    return jsonify({'status': 'checked'})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


@app.route('/debug/payment-check')
@login_required
def debug_payment_check():
    """Debug endpoint to check payment data"""
    conn = db_manager.get_connection()
    debug_info = {
        'current_user_id': current_user.id,
        'connection': 'Failed',
        'columns': [],
        'won_auctions_all': [],
        'pending_payments': [],
        'error': None
    }

    if conn:
        debug_info['connection'] = 'Success'
        try:
            cursor = conn.cursor(dictionary=True)

            # Check table columns
            cursor.execute("DESCRIBE auctions")
            debug_info['columns'] = [col['Field'] for col in cursor.fetchall()]

            # Get all won auctions
            cursor.execute("""
                SELECT auction_id, title, status, winner_id,
                       payment_status, sold_price, current_bid, end_time
                FROM auctions
                WHERE winner_id = %s
                ORDER BY end_time DESC
            """, (current_user.id,))
            debug_info['won_auctions_all'] = cursor.fetchall()

            # Get pending payments using the same query as get_pending_payments
            cursor.execute("""
                SELECT a.auction_id, a.title, a.status,
                       a.payment_status, a.sold_price, a.current_bid,
                       COALESCE(a.sold_price, a.current_bid) as final_price
                FROM auctions a
                WHERE a.winner_id = %s
                AND a.status IN ('completed', 'sold')
                AND (a.payment_status IS NULL OR a.payment_status = 'pending')
                ORDER BY a.end_time DESC
            """, (current_user.id,))
            debug_info['pending_payments'] = cursor.fetchall()

        except Exception as e:
            debug_info['error'] = str(e)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return jsonify(debug_info)

# Template filters
@app.template_filter('timeago')
def timeago_filter(dt):
    """Convert datetime to time ago string"""
    if not dt:
        return ''
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 7:
        return dt.strftime('%B %d, %Y')
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

@app.template_filter('countdown')
def countdown_filter(dt):
    """Convert datetime or timedelta to countdown string"""
    if not dt:
        return ''

    now = datetime.now()

    # ✅ Handle both datetime and timedelta safely
    if isinstance(dt, timedelta):
        diff = dt
    elif isinstance(dt, datetime):
        diff = dt - now
    else:
        return ''

    # ✅ Ensure we don't show negative countdowns
    if diff.total_seconds() <= 0:
        return "Ended"

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # ✅ Friendly formatting
    if days > 0:
        return f"{days} day{'s' if days > 1 else ''} left"
    elif hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} left"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} left"
    else:
        return f"{seconds} seconds left"

@app.template_filter('currency')
def currency_filter(value):
    """Format value as currency"""
    return f"${value:,.2f}" if value else "$0.00"

@app.template_filter('regex_search')
def regex_search_filter(text, pattern):
    """Extract text using regex pattern"""
    import re
    match = re.search(pattern, text)
    return match.group(1) if match else None

# Background task to close expired auctions (run this periodically)
def close_expired_auctions_task():
    """Task to close expired auctions - should be run periodically"""
    with app.app_context():
        db_manager.close_expired_auctions()

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Run the application
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)