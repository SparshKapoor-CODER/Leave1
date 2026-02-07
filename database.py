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
        
        if db_url and 'mysql://' in db_url:
            # Parse Railway DATABASE_URL format: mysql://user:password@host:port/database
            parsed = urlparse(db_url)
            self.host = parsed.hostname
            self.user = parsed.username
            self.password = parsed.password
            self.database = parsed.path[1:]  # Remove leading '/'
            self.port = parsed.port or 3306
        else:
            # Fall back to individual environment variables (for local development)
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
                connect_timeout=10  # Add timeout for Railway
            )
            print("✓ Database connection successful!")
            return connection
        except pymysql.err.OperationalError as e:
            print(f"✗ Database connection failed: {e}")
            print("\nTroubleshooting:")
            print(f"1. Check if MySQL is running at {self.host}:{self.port}")
            print(f"2. Verify credentials for user '{self.user}'")
            print(f"3. Check if database '{self.database}' exists")
            
            # For Railway-specific help
            if 'railway.app' in str(self.host):
                print("4. Railway MySQL: Ensure service is running and variables are set")
                print("   - Check Railway Dashboard → MySQL → Connect")
                print("   - Copy DATABASE_URL from connection details")
            
            raise
        except Exception as e:
            print(f"✗ Unexpected database error: {e}")
            traceback.print_exc()
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
                # Create database if not exists (only for local MySQL)
                if 'localhost' in self.host or '127.0.0.1' in self.host:
                    try:
                        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                        cursor.execute(f"USE {self.database}")
                        print(f"✓ Database '{self.database}' created/selected successfully!")
                    except Exception as e:
                        print(f"Note: Could not create database (may already exist): {e}")
                        cursor.execute(f"USE {self.database}")
                else:
                    # For Railway, just use the existing database
                    cursor.execute(f"USE {self.database}")
                
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
                
                # Create leaves table
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
                        qr_token VARCHAR(100) UNIQUE,
                        qr_expiry TIMESTAMP NULL,
                        verification_count INT DEFAULT 0,
                        suspicious_flag BOOLEAN DEFAULT FALSE,
                        flagged_by VARCHAR(50),
                        flag_reason TEXT,
                        flagged_at TIMESTAMP NULL
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

                # Create admin_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admin_logs (
                        log_id INT AUTO_INCREMENT PRIMARY KEY,
                        admin_id VARCHAR(20) NOT NULL,
                        action_type VARCHAR(50) NOT NULL,
                        target_type VARCHAR(50) NOT NULL,
                        target_id VARCHAR(50),
                        details TEXT,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                print("✓ Created/Verified 'admin_logs' table")

                # Create admin_leave_flags table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admin_leave_flags (
                        flag_id INT AUTO_INCREMENT PRIMARY KEY,
                        leave_id INT NOT NULL,
                        flagged_by VARCHAR(50) NOT NULL,
                        reason TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (leave_id) REFERENCES leaves(leave_id) ON DELETE CASCADE,
                        FOREIGN KEY (flagged_by) REFERENCES admins(admin_id) ON DELETE CASCADE
                    )
                ''')
                print("✓ Created/Verified 'admin_leave_flags' table")

                # Create parent_contacts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_contacts (
                        contact_id INT AUTO_INCREMENT PRIMARY KEY,
                        leave_id INT NOT NULL,
                        contact_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        method VARCHAR(50),
                        confirmation_code VARCHAR(100),
                        notes TEXT,
                        FOREIGN KEY (leave_id) REFERENCES leaves(leave_id) ON DELETE CASCADE
                    )
                ''')
                print("✓ Created/Verified 'parent_contacts' table")

                # Create leave_audit_log table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leave_audit_log (
                        log_id INT AUTO_INCREMENT PRIMARY KEY,
                        leave_id INT NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        performed_by VARCHAR(100) NOT NULL,
                        performed_by_type VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT,
                        FOREIGN KEY (leave_id) REFERENCES leaves(leave_id) ON DELETE CASCADE
                    )
                ''')
                print("✓ Created/Verified 'leave_audit_log' table")
                
                connection.commit()
                print("\n" + "="*50)
                print("ALL TABLES CREATED/VERIFIED SUCCESSFULLY!")
                print("✓ 10 tables initialized")
                print("="*50 + "\n")
                
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            traceback.print_exc()
            if connection:
                connection.rollback()
            
            # For Railway, we might not have all permissions to create tables
            # So just continue and hope tables exist
            print("\n⚠ Note: Some tables might already exist or permissions issue.")
            print("Continuing with application...")
        finally:
            if connection:
                connection.close()