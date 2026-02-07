# [file name]: database.py
import pymysql
import os
from dotenv import load_dotenv
import bcrypt
import traceback
from urllib.parse import urlparse

# Load environment variables
load_dotenv('.env')

class Database:
    def __init__(self):
        # Try to get DATABASE_URL from Railway first
        db_url = os.getenv('DATABASE_URL')
        
        if db_url:
            # Check if it's a full URL or just hostname
            if '://' in db_url:
                # Parse DATABASE_URL format: mysql://user:password@host:port/database
                parsed = urlparse(db_url)
                self.host = parsed.hostname
                self.user = parsed.username
                self.password = parsed.password
                self.database = parsed.path[1:] if parsed.path.startswith('/') else parsed.path
                self.port = parsed.port or 3306
            else:
                # It's just a hostname
                self.host = db_url
                self.user = os.getenv('DB_USER', 'root')
                self.password = os.getenv('DB_PASSWORD', '')
                self.database = os.getenv('DB_NAME', 'vit_leave_management')
                self.port = int(os.getenv('DB_PORT', 3306))
        else:
            # Fall back to individual environment variables
            self.host = os.getenv('DB_HOST', 'localhost')
            self.user = os.getenv('DB_USER', 'root')
            self.password = os.getenv('DB_PASSWORD', '')
            self.database = os.getenv('DB_NAME', 'vit_leave_management')
            self.port = int(os.getenv('DB_PORT', 3306))
        
        # Debug: Show connection details
        print("\n" + "="*50)
        print("DATABASE CONNECTION DETAILS:")
        print(f"Host: {self.host}")
        print(f"User: {self.user}")
        print(f"Password: {'*' * len(self.password) if self.password else '(empty)'}")
        print(f"Database: {self.database}")
        print(f"Port: {self.port}")
        print("="*50 + "\n")
        
    def get_connection(self):
        try:
            connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                charset='utf8mb4',
                connect_timeout=10
            )
            print("✓ Database connection successful!")
            return connection
        except pymysql.err.OperationalError as e:
            print(f"✗ Database connection failed: {e}")
            print(f"\nCurrent connection details:")
            print(f"  Host: {self.host}")
            print(f"  User: {self.user}")
            print(f"  Port: {self.port}")
            print(f"  Database: {self.database}")
            print(f"\nTroubleshooting:")
            print("  1. Check if hostname is correct (not a full URL)")
            print("  2. Verify port number (not 3306 for Railway)")
            print("  3. Check if database name is 'railway'")
            print("  4. Ensure Railway MySQL service is running")
            raise
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def check_password(hashed_password, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            print(f"Password check error: {e}")
            return False
    
    def init_db(self):
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # For Railway, we don't create database, just use it
                cursor.execute(f"USE {self.database}")
                print(f"✓ Using database: {self.database}")
                
                # Try to create tables (they might already exist)
                tables = [
                    ('students', '''
                        CREATE TABLE IF NOT EXISTS students (
                            reg_number VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            proctor_id VARCHAR(20) NOT NULL,
                            hostel_block VARCHAR(10) NOT NULL,
                            room_number VARCHAR(10) NOT NULL,
                            phone VARCHAR(15),
                            parent_phone VARCHAR(15)
                        )
                    '''),
                    ('proctors', '''
                        CREATE TABLE IF NOT EXISTS proctors (
                            employee_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            email VARCHAR(100),
                            department VARCHAR(100)
                        )
                    '''),
                    ('leaves', '''
                        CREATE TABLE IF NOT EXISTS leaves (
                            leave_id INT AUTO_INCREMENT PRIMARY KEY,
                            student_reg VARCHAR(20) NOT NULL,
                            proctor_id VARCHAR(20) NOT NULL,
                            leave_type ENUM('emergency', 'regular', 'medical') NOT NULL,
                            from_date DATE NOT NULL,
                            to_date DATE NOT NULL,
                            from_time TIME NOT NULL,
                            to_time TIME NOT NULL,
                            reason TEXT NOT NULL,
                            destination VARCHAR(200),
                            parent_contacted BOOLEAN DEFAULT FALSE,
                            status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            approved_at TIMESTAMP NULL,
                            qr_token VARCHAR(100) UNIQUE,
                            qr_expiry TIMESTAMP NULL,
                            verification_count INT DEFAULT 0,
                            suspicious_flag BOOLEAN DEFAULT FALSE,
                            flagged_by VARCHAR(50),
                            flag_reason TEXT,
                            flagged_at TIMESTAMP NULL
                        )
                    '''),
                    ('hostel_supervisors', '''
                        CREATE TABLE IF NOT EXISTS hostel_supervisors (
                            supervisor_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            hostel_block VARCHAR(10) NOT NULL,
                            email VARCHAR(100)
                        )
                    '''),
                    ('admins', '''
                        CREATE TABLE IF NOT EXISTS admins (
                            admin_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            email VARCHAR(100),
                            role ENUM('super_admin', 'admin', 'moderator') DEFAULT 'admin',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                ]
                
                for table_name, create_sql in tables:
                    try:
                        cursor.execute(create_sql)
                        print(f"✓ Created/Verified '{table_name}' table")
                    except Exception as e:
                        print(f"⚠ Note creating '{table_name}': {e}")
                        # Continue anyway
                
                connection.commit()
                print("\n" + "="*50)
                print("DATABASE INITIALIZED SUCCESSFULLY!")
                print("="*50 + "\n")
                
        except Exception as e:
            print(f"✗ Error initializing database: {e}")
            print("⚠ Continuing without database...")
        finally:
            if 'connection' in locals():
                connection.close()