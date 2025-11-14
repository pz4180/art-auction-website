#!/usr/bin/env python3
"""
Database Wallet System Checker
This script checks if the wallet system is properly configured in MySQL
"""

import mysql.connector
from mysql.connector import Error
from config import Config

def check_wallet_setup():
    """Check if wallet system is properly configured"""
    print("=" * 60)
    print("WALLET SYSTEM DATABASE CHECKER")
    print("=" * 60)

    try:
        # Connect to database
        print(f"\n1. Connecting to database...")
        print(f"   Host: {Config.MYSQL_HOST}")
        print(f"   Database: {Config.MYSQL_DATABASE}")
        print(f"   User: {Config.MYSQL_USER}")

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            port=Config.MYSQL_PORT
        )

        if conn.is_connected():
            print("   ✓ Successfully connected to database")
            cursor = conn.cursor(dictionary=True)

            # Check MySQL version
            cursor.execute("SELECT VERSION() as version")
            version = cursor.fetchone()
            print(f"\n2. MySQL Version: {version['version']}")

            # Check if users table exists
            print("\n3. Checking users table...")
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'
            """, (Config.MYSQL_DATABASE,))
            result = cursor.fetchone()
            if result['count'] > 0:
                print("   ✓ Users table exists")
            else:
                print("   ✗ Users table NOT found!")
                return

            # Check if wallet_balance column exists
            print("\n4. Checking wallet_balance column...")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, IS_NULLABLE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'users'
                AND COLUMN_NAME = 'wallet_balance'
            """, (Config.MYSQL_DATABASE,))
            result = cursor.fetchone()
            if result:
                print(f"   ✓ wallet_balance column exists")
                print(f"     Type: {result['DATA_TYPE']}")
                print(f"     Default: {result['COLUMN_DEFAULT']}")
            else:
                print("   ✗ wallet_balance column NOT found!")
                print("   → Run setup_wallet_mysql.sql to add it")
                return

            # Check if wallet_transactions table exists
            print("\n5. Checking wallet_transactions table...")
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'wallet_transactions'
            """, (Config.MYSQL_DATABASE,))
            result = cursor.fetchone()
            if result['count'] > 0:
                print("   ✓ wallet_transactions table exists")

                # Check table structure
                cursor.execute("DESCRIBE wallet_transactions")
                columns = cursor.fetchall()
                print(f"\n   Table structure:")
                for col in columns:
                    print(f"     - {col['Field']}: {col['Type']}")

                # Count transactions
                cursor.execute("SELECT COUNT(*) as count FROM wallet_transactions")
                result = cursor.fetchone()
                print(f"\n   Total transactions: {result['count']}")
            else:
                print("   ✗ wallet_transactions table NOT found!")
                print("   → Run setup_wallet_mysql.sql to create it")
                return

            # Check user count
            print("\n6. Checking users...")
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            print(f"   Total users: {result['count']}")

            if result['count'] > 0:
                cursor.execute("""
                    SELECT user_id, username, wallet_balance
                    FROM users
                    LIMIT 5
                """)
                users = cursor.fetchall()
                print("\n   Sample user balances:")
                for user in users:
                    print(f"     - User #{user['user_id']} ({user['username']}): RM{user['wallet_balance']}")

            print("\n" + "=" * 60)
            print("✓ WALLET SYSTEM IS PROPERLY CONFIGURED!")
            print("=" * 60)

    except Error as e:
        print(f"\n✗ Database Error: {e}")
        print("\nPossible solutions:")
        print("1. Check if MySQL server is running")
        print("2. Verify database credentials in config.py or .env")
        print("3. Run setup_wallet_mysql.sql to set up wallet system")
        print("4. Check if database 'art_auction_db' exists")

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    check_wallet_setup()
