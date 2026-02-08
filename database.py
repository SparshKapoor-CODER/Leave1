# [file name]: database.py
import pymysql
import os
from dotenv import load_dotenv
import bcrypt
import traceback
from urllib.parse import urlparse

# Load environment variables for local development
load_dotenv('.env')

class Database:
    def __init__(self):
        # Try to get MYSQL_URL from Railway first
        mysql_url = os.getenv('MYSQL_URL')
        
        if mysql_url:
            # Parse the MySQL URL from Railway
            parsed = urlparse(mysql_url)
            self.host = parsed.hostname
            self.user = parsed.username
            self.password = parsed.password
            self.database = parsed.path[1:] if parsed.path else 'railway'
            self.port = parsed.port or 3306
        else:
            # Fallback to individual variables (for local development)
            self.host = os.getenv('DB_HOST', 'localhost')
            self.user = os.getenv('DB_USER', 'root')
            self.password = os.getenv('DB_PASSWORD', '')
            self.database = os.getenv('DB_NAME', 'vit_leave_management')
            self.port = int(os.getenv('DB_PORT', 3306))
        
        # Debug: Show connection details (mask password)
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
            print(f"\nTroubleshooting:")
            print(f"1. Check if MySQL service is running in Railway")
            print(f"2. MYSQL_URL variable: {os.getenv('MYSQL_URL', 'Not set')}")
            print(f"3. Trying to connect to: {self.host}:{self.port}")
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
        connection = None
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # Don't create database - use the one provided by Railway
                # Just create tables if they don't exist
                
                # Create students table
                cursor.execute('''
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
                ''')
                print("✓ Created/Verified 'students' table")
                
                # Create proctors table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctors (
                        employee_id VARCHAR(20) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        department VARCHAR(100)
                    )
                ''')
                print("✓ Created/Verified 'proctors' table")
                
                # Create leaves table (simplified for Railway)
                cursor.execute('''
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
                        qr_token VARCHAR(100),
                        qr_expiry TIMESTAMP NULL,
                        verification_count INT DEFAULT 0,
                        suspicious_flag BOOLEAN DEFAULT FALSE
                    )
                ''')
                print("✓ Created/Verified 'leaves' table")
                
                # Create hostel_supervisors table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS hostel_supervisors (
                        supervisor_id VARCHAR(20) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        hostel_block VARCHAR(10) NOT NULL,
                        email VARCHAR(100)
                    )
                ''')
                print("✓ Created/Verified 'hostel_supervisors' table")

                # Create admins table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        admin_id VARCHAR(20) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        role ENUM('super_admin', 'admin', 'moderator') DEFAULT 'admin',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                print("✓ Created/Verified 'admins' table")

                # Create verification_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS verification_logs (
                        log_id INT AUTO_INCREMENT PRIMARY KEY,
                        leave_id INT,
                        supervisor_id VARCHAR(20),
                        verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        action ENUM('granted', 'rejected', 'suspicious', 'flagged') NOT NULL,
                        notes TEXT
                    )
                ''')
                print("✓ Created/Verified 'verification_logs' table")

                connection.commit()
                print("\n" + "="*50)
                print("ALL TABLES CREATED/VERIFIED SUCCESSFULLY!")
                print("✓ 6 essential tables created")
                print("="*50 + "\n")
                
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            traceback.print_exc()
            # Don't raise here - let the app continue without tables
            print("⚠ Continuing in limited mode...")
        finally:
            if connection:
                connection.close()