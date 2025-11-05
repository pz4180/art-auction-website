from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import os
import json
from PIL import Image
from config import Config
from db_operations import db_manager

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

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Helper function to resize and save images
def save_artwork_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Save and optimize image
        img = Image.open(file)
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Resize if too large
        max_size = (1200, 1200)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        img.save(filepath, 'JPEG', quality=85, optimize=True)
        
        return filename
    return None

# Routes

@app.route('/')
def index():
    """Home page showing featured auctions"""
    auctions = db_manager.get_active_auctions(limit=6)
    if current_user.is_authenticated:
        notifications = db_manager.get_user_notifications(current_user.id, unread_only=True)
    else:
        notifications = []
    return render_template('index.html', auctions=auctions, notifications=notifications)

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
    
    # Mark notifications as read
    db_manager.mark_notifications_read(current_user.id)
    
    return render_template('dashboard.html', 
                         my_auctions=my_auctions,
                         my_bids=my_bids,
                         won_auctions=won_auctions,
                         notifications=notifications)

@app.route('/create_auction', methods=['GET', 'POST'])
@login_required
def create_auction():
    """Create new auction page"""
    categories = db_manager.get_categories()
    
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
                    flash('Error uploading image', 'danger')
            else:
                flash('Invalid file type. Please upload an image.', 'danger')
    
    return render_template('create_auction.html', categories=categories)

@app.route('/browse')
def browse_auctions():
    """Browse all active auctions with search and filter"""
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search_term = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    # Pagination
    per_page = 12
    offset = (page - 1) * per_page
    
    # Get auctions
    auctions = db_manager.get_active_auctions(
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search_term=search_term if search_term else None,
        limit=per_page,
        offset=offset
    )
    
    # Get categories for filter
    categories = db_manager.get_categories()
    
    return render_template('browse_auctions.html', 
                         auctions=auctions,
                         categories=categories,
                         current_category=category_id,
                         search_term=search_term,
                         min_price=min_price,
                         max_price=max_price,
                         page=page)

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
    
    return render_template('auction_history.html',
                         my_past_auctions=my_past_auctions,
                         my_bid_history=my_bid_history,
                         won_auctions=won_auctions)

@app.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint to get user notifications"""
    notifications = db_manager.get_user_notifications(current_user.id, unread_only=True)
    return jsonify({
        'count': len(notifications),
        'notifications': notifications
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
