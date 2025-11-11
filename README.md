# Art Auction Website

A complete web-based art auction platform built with Python (Flask), MySQL, and Bootstrap. This platform allows users to create accounts, upload artwork for auction, browse and bid on items, and receive notifications about auction activities.

## Features

### System Functions
1. **User Registration & Authentication**
   - Secure user registration with username, email, and password
   - Login/logout functionality with session management
   - Password strength validation

2. **Upload Artwork and Create Auction**
   - Upload artwork images with details
   - Set starting bid price and auction duration
   - Automatic image optimization and resizing

3. **Auction Browsing and Search**
   - Browse all active auctions
   - Filter by category, price range
   - Search functionality
   - Grid and list view options

4. **Bidding System**
   - Real-time bidding on active auctions
   - Automatic outbid notifications
   - Minimum bid increment enforcement
   - Winner announcement when auction ends

5. **Auction Results and History**
   - View completed auctions
   - Personal bidding history
   - Won auctions tracking
   - Detailed auction statistics

6. **Notifications and Alerts**
   - Real-time notifications for:
     - Being outbid
     - Winning an auction
     - New auctions created
   - Dashboard and email notification options

## Technology Stack

- **Backend:** Python 3.x with Flask framework
- **Database:** MySQL
- **Frontend:** HTML5, CSS3, JavaScript with Bootstrap 5
- **Additional:** Pillow for image processing

## Color Scheme

The website uses a warm, artistic color palette:
- Primary: `#7E3B21` (Dark Brown)
- Secondary: `#D99D76` (Light Brown)
- Accent: `#EBCCA0` (Beige)
- Support: `#848154` (Olive)
- Neutral: `#C29E7B` (Tan)
- Dark: `#785D54` (Dark Taupe)

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

### Step 1: Clone/Download the Project
```bash
# Create a new directory for your project
mkdir art-auction-website
cd art-auction-website

# Copy all the provided files to this directory
```

### Step 2: Set Up Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up MySQL Database
1. Log into MySQL:
```bash
mysql -u root -p
```

2. Run the database.sql script:
```sql
source database.sql
```

Or manually create the database:
```sql
CREATE DATABASE art_auction_db;
USE art_auction_db;
-- Then run all the CREATE TABLE statements from database.sql
```

### Step 5: Configure Database Connection
Edit `config.py` and update the MySQL credentials:
```python
MYSQL_USER = 'your_mysql_username'
MYSQL_PASSWORD = 'your_mysql_password'
MYSQL_DATABASE = 'art_auction_db'
MYSQL_HOST = 'localhost'
```

### Step 6: Create Required Directories
The application will create these automatically, but you can create them manually:
```bash
mkdir -p static/uploads
```

### Step 7: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

## Project Structure

```
art-auction-website/
│
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── database.sql             # MySQL database schema
├── db_operations.py         # Database operations module
│
├── static/                  # Static files
│   ├── css/
│   │   └── style.css       # Custom styles
│   ├── js/
│   │   └── main.js         # Custom JavaScript
│   └── uploads/            # Uploaded artwork images
│
└── templates/              # HTML templates
    ├── base.html          # Base template
    ├── index.html         # Home page
    ├── register.html      # Registration page
    ├── login.html         # Login page
    ├── dashboard.html     # User dashboard
    ├── create_auction.html # Create auction page
    ├── auction_detail.html # Auction details page
    ├── browse_auctions.html # Browse auctions page
    └── auction_history.html # Auction history page
```

## Usage Guide

### For Users:
1. **Register an Account**
   - Click "Sign Up" on the navigation bar
   - Enter username, email, and password
   - Confirm your password and accept terms

2. **Create an Auction**
   - Login to your account
   - Click "Create Auction" from dashboard or navigation
   - Fill in artwork details:
     - Title and description
     - Select category
     - Upload image (max 16MB)
     - Set starting bid price
     - Choose auction duration (3-14 days)
   - Submit to create auction

3. **Browse and Bid**
   - Browse auctions from the home page or "Browse" section
   - Use filters to find specific items:
     - Category filter
     - Price range
     - Search by keyword
   - Click on an auction to view details
   - Place your bid (must be higher than current bid + minimum increment)

4. **Track Your Activity**
   - Dashboard shows:
     - Your active auctions
     - Current bids
     - Won auctions
     - Recent notifications
   - History page shows all past activities

### For Administrators:
- Access the database directly to:
  - Add new categories
  - Moderate auctions
  - View system statistics
  - Manage users

## API Endpoints

The application includes several API endpoints:
- `/api/notifications` - Get user notifications
- `/api/mark_notifications_read` - Mark notifications as read
- `/api/check_auction_status` - Check and update auction statuses

## Security Features

- Password hashing using Werkzeug security
- Session management with Flask-Login
- CSRF protection
- SQL injection prevention through parameterized queries
- File upload validation and size limits
- Secure file naming for uploads

## Customization

### Adding New Categories
Add categories in the database:
```sql
INSERT INTO categories (category_name) VALUES ('New Category');
```

### Changing Auction Settings
Edit `config.py`:
```python
DEFAULT_AUCTION_DURATION_DAYS = 7
MINIMUM_BID_INCREMENT = 5.00
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

### Email Notifications (Optional)
Configure email settings in `config.py`:
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_app_password'
```

## Troubleshooting

### Common Issues:

1. **Database Connection Error**
   - Verify MySQL is running
   - Check credentials in config.py
   - Ensure database exists

2. **Image Upload Issues**
   - Check file permissions on static/uploads directory
   - Verify file size is under 16MB
   - Ensure file format is supported (JPG, PNG, GIF, WEBP)

3. **Port Already in Use**
   - Change port in app.py: `app.run(port=5001)`

4. **Module Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using the virtual environment

## Development Notes

- The application runs in debug mode by default (change in config.py for production)
- Auction status updates should be run periodically (consider using a scheduler like APScheduler)
- For production, use a proper WSGI server like Gunicorn
- Consider implementing Redis for caching and real-time notifications
- Add email verification for user registration in production

## Future Enhancements

- Payment integration (Stripe/PayPal)
- Real-time bidding with WebSockets
- Mobile app development
- Advanced analytics dashboard
- Social media integration
- Multi-language support
- Auction preview/draft mode
- Bulk upload functionality
- Advanced search with AI recommendations

## Support

For issues or questions about the implementation, please refer to the inline code comments or create an issue in your project repository.
https://www.nga.gov/artworks/74796-japanese-footbridge

---
venv\Scripts\activate
python app.py
ngrok http 5000

