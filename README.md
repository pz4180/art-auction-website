# 🎨 Art Auction Website

A full-featured web-based art auction platform that enables users to create accounts, upload artwork, participate in auctions, and receive real-time notifications about bidding activities.

## 📋 Table of Contents

- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Project Structure](#-project-structure)
- [Usage Guide](#-usage-guide)
- [Configuration](#-configuration)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Future Enhancements](#-future-enhancements)

## ✨ Features

### User Management
- **Secure Authentication**: Registration and login with password hashing and session management
- **User Profiles**: Personal dashboard showing active auctions, bids, and won items
- **Notification System**: Real-time alerts for outbids, auction wins, and new listings

### Auction Management
- **Create Auctions**: Upload artwork with automatic image optimization and set auction parameters
- **Browse & Search**: Filter by category, price range, and keywords with grid/list view options
- **Real-time Bidding**: Live bidding system with automatic outbid notifications and minimum increment enforcement
- **Auction History**: Complete tracking of past auctions, bids, and results

### Artwork Handling
- **Image Upload**: Support for JPG, PNG, GIF, and WEBP formats (up to 16MB)
- **Automatic Processing**: Image optimization and resizing for web display
- **Gallery Views**: Multiple display options for browsing artwork

## 🛠 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.8+ with Flask |
| **Database** | MySQL 5.7+ |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Image Processing** | Pillow (PIL) |
| **Authentication** | Flask-Login, Werkzeug Security |

### Color Palette

The website features a warm, artistic color scheme:

```css
Primary:   #7E3B21  /* Dark Brown */
Secondary: #D99D76  /* Light Brown */
Accent:    #EBCCA0  /* Beige */
Support:   #848154  /* Olive */
Neutral:   #C29E7B  /* Tan */
Dark:      #785D54  /* Dark Taupe */
```

## 📦 Installation

### Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd art-auction-website
   ```

2. **Create Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL Database**

   Log into MySQL and create the database:
   ```bash
   mysql -u root -p
   ```

   Then run the database script:
   ```sql
   source database.sql
   ```

   Or create manually:
   ```sql
   CREATE DATABASE art_auction_db;
   USE art_auction_db;
   -- Run CREATE TABLE statements from database.sql
   ```

5. **Configure Application**

   Edit `config.py` with your MySQL credentials:
   ```python
   MYSQL_USER = 'your_mysql_username'
   MYSQL_PASSWORD = 'your_mysql_password'
   MYSQL_DATABASE = 'art_auction_db'
   MYSQL_HOST = 'localhost'
   ```

6. **Create Upload Directory**
   ```bash
   mkdir -p static/uploads
   ```

7. **Run the Application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

## 📁 Project Structure

```
art-auction-website/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── database.sql               # MySQL database schema
├── db_operations.py           # Database operations
├── static/
│   ├── css/
│   │   └── style.css         # Custom styles
│   ├── js/
│   │   └── main.js           # Custom JavaScript
│   ├── images/               # Static images
│   └── uploads/              # User-uploaded artwork
└── templates/
    ├── base.html             # Base template
    ├── index.html            # Home page
    ├── register.html         # Registration
    ├── login.html            # Login
    ├── dashboard.html        # User dashboard
    ├── create_auction.html   # Create auction
    ├── auction_detail.html   # Auction details
    ├── browse_auctions.html  # Browse auctions
    └── auction_history.html  # Auction history
```

## 📖 Usage Guide

### For Bidders

1. **Register an Account**
   - Navigate to the Sign Up page
   - Enter username, email, and password
   - Confirm password and accept terms

2. **Browse Auctions**
   - View all active auctions from the home page
   - Use filters for category, price range, or keywords
   - Switch between grid and list views

3. **Place Bids**
   - Click on an auction to view details
   - Enter your bid (must exceed current bid + minimum increment)
   - Receive notifications if outbid

4. **Track Your Activity**
   - Visit your dashboard to view:
     - Active bids
     - Won auctions
     - Notifications
     - Bidding history

### For Sellers

1. **Create an Auction**
   - Login and navigate to "Create Auction"
   - Fill in artwork details:
     - Title and description
     - Category selection
     - Upload image (max 16MB)
     - Set starting bid price
     - Choose duration (3-14 days)
   - Submit to publish

2. **Manage Your Auctions**
   - View active auctions from your dashboard
   - Monitor current bids
   - Check auction status
   - View final results when auction ends

## ⚙️ Configuration

### Auction Settings

Edit `config.py` to customize:

```python
# Auction duration
DEFAULT_AUCTION_DURATION_DAYS = 7

# Minimum bid increment
MINIMUM_BID_INCREMENT = 5.00

# File upload limits
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### Email Notifications (Optional)

Configure email settings for notifications:

```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_app_password'
MAIL_USE_TLS = True
```

### Adding Categories

Add new artwork categories via MySQL:

```sql
INSERT INTO categories (category_name) VALUES ('New Category');
```

## 🔒 Security

The application implements multiple security measures:

- **Password Security**: Hashing with Werkzeug
- **Session Management**: Flask-Login integration
- **SQL Injection Prevention**: Parameterized queries
- **File Upload Validation**: Type and size restrictions
- **CSRF Protection**: Built-in Flask security
- **Secure File Naming**: Sanitized upload filenames

## 🐛 Troubleshooting

### Database Connection Error
- Verify MySQL is running: `sudo service mysql status`
- Check credentials in `config.py`
- Ensure `art_auction_db` database exists

### Image Upload Issues
- Check permissions: `chmod 755 static/uploads`
- Verify file size is under 16MB
- Confirm file format is supported

### Port Already in Use
- Change port in `app.py`:
  ```python
  app.run(port=5001)
  ```

### Module Import Errors
- Ensure virtual environment is active
- Reinstall dependencies: `pip install -r requirements.txt`

## 🚀 Future Enhancements

- [ ] Payment integration (Stripe/PayPal)
- [ ] Real-time bidding with WebSockets
- [ ] Mobile responsive design improvements
- [ ] Advanced analytics dashboard
- [ ] Social media sharing
- [ ] Multi-language support
- [ ] Auction preview/draft mode
- [ ] Bulk upload functionality
- [ ] AI-powered artwork recommendations
- [ ] Automated email verification
- [ ] Admin moderation panel

## 📄 License

This project is available for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Note**: This application runs in debug mode by default. For production deployment:
- Set `DEBUG = False` in `config.py`
- Use a production WSGI server (e.g., Gunicorn)
- Implement proper logging and monitoring
- Add Redis for caching and real-time features
- Enable email verification for user registration
