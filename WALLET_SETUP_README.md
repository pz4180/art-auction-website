# Wallet Top-Up Issue - Fix Guide

## Problem
You cannot top up your wallet even when entering correct numbers. This is likely due to:
1. Missing database tables or columns for the wallet system
2. Incompatible MySQL migration scripts
3. Input validation or data type issues

## Solution

### Step 1: Check Database Configuration

Run the database checker script:
```bash
python check_wallet_db.py
```

This will verify:
- Database connection
- MySQL version
- `wallet_balance` column in `users` table
- `wallet_transactions` table existence
- Current user balances

### Step 2: Set Up Wallet System (if needed)

If the checker reports missing tables/columns, run the setup script:

```bash
mysql -u root -p art_auction_db < setup_wallet_mysql.sql
```

Or manually in MySQL:
```bash
mysql -u root -p
```
```sql
USE art_auction_db;
SOURCE /home/user/art-auction-website/setup_wallet_mysql.sql;
```

The new `setup_wallet_mysql.sql` script is compatible with MySQL 5.7+ and 8.0+ (unlike the old scripts that used MySQL 8.0.31+ specific syntax).

### Step 3: Test the Application

1. Start your Flask application:
   ```bash
   python app.py
   ```

2. Log in to your account

3. Navigate to the Wallet page

4. Try to top up with a valid amount (e.g., 100)

### What Was Fixed

1. **Improved MySQL Compatibility** (`setup_wallet_mysql.sql`):
   - Uses stored procedure to safely check and add columns
   - Compatible with MySQL 5.7+ and all MySQL 8.x versions
   - Properly handles existing columns/tables

2. **Better Error Handling** (`app.py`):
   - Validates empty input before conversion
   - Catches Decimal conversion errors
   - Provides clearer error messages
   - Shows database configuration issues

3. **Validation Messages** (`app.py`, `wallet.html`):
   - Fixed incorrect maximum amount messages
   - Now correctly shows RM1,000,000.00 limit

### Validation Rules

- **Minimum**: RM10.00
- **Maximum**: RM1,000,000.00
- Amount must be a valid number with up to 2 decimal places

### Common Error Messages

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Please enter an amount" | Empty input field | Enter a number |
| "Invalid amount format" | Non-numeric input | Enter a valid number |
| "Amount must be greater than zero" | Entered 0 or negative | Enter a positive amount |
| "Minimum top-up amount is RM10.00" | Amount < 10 | Enter at least 10 |
| "Maximum top-up amount is RM1,000,000.00" | Amount > 1,000,000 | Enter less than 1,000,000 |
| "Failed to top-up wallet. Please check if the wallet system is properly configured" | Database error | Run setup script |

### Troubleshooting

#### If top-up still doesn't work:

1. **Check MySQL logs** for errors:
   ```bash
   sudo tail -f /var/log/mysql/error.log
   ```

2. **Check Flask console output** for detailed error messages (now includes full traceback)

3. **Verify database credentials** in `config.py` or `.env`:
   - MYSQL_HOST
   - MYSQL_USER
   - MYSQL_PASSWORD
   - MYSQL_DATABASE

4. **Test database connection**:
   ```bash
   mysql -u root -p
   USE art_auction_db;
   SHOW TABLES;
   DESCRIBE users;
   DESCRIBE wallet_transactions;
   ```

5. **Check if wallet_balance column exists**:
   ```sql
   SHOW COLUMNS FROM users LIKE 'wallet_balance';
   ```

   If empty result, run the setup script again.

## Files Modified/Created

- ✓ `setup_wallet_mysql.sql` - New MySQL-compatible setup script
- ✓ `check_wallet_db.py` - Database verification tool
- ✓ `app.py` - Improved validation and error handling
- ✓ `templates/wallet.html` - Fixed validation messages
- ✓ `WALLET_SETUP_README.md` - This guide

## Support

If you continue to experience issues:
1. Run `python check_wallet_db.py` and share the output
2. Check the Flask console for error messages
3. Verify your MySQL version: `mysql --version`
