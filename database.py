# [file name]: database.py
import pymysql
import os
from dotenv import load_dotenv
import bcrypt
import traceback
from urllib.parse import urlparse
from threading import Lock
import time

# Load environment variables for local development
load_dotenv('.env')

class Database:
    # Singleton connection pool
    _connection_pool = None
    _lock = Lock()
    
    def __init__(self):
        # First, check for Railway's standard MySQL environment variables
        self.host = os.getenv('MYSQLHOST')
        self.user = os.getenv('MYSQLUSER')
        self.password = os.getenv('MYSQLPASSWORD')
        self.database = os.getenv('MYSQLDATABASE')
        self.port = int(os.getenv('MYSQLPORT', 3306))
        
        print(f"DEBUG: MYSQLHOST: {self.host}")
        print(f"DEBUG: MYSQLUSER: {self.user}")
        print(f"DEBUG: MYSQLDATABASE: {self.database}")
        print(f"DEBUG: MYSQLPORT: {self.port}")
        
        # If Railway variables are not set, try MYSQL_URL
        if not all([self.host, self.user, self.password, self.database]):
            mysql_url = os.getenv('MYSQL_URL')
            print(f"DEBUG: MYSQL_URL: {mysql_url}")
            
            if mysql_url:
                try:
                    # Parse the MySQL URL from Railway
                    if mysql_url.startswith('mysql://'):
                        parsed = urlparse(mysql_url)
                        self.host = parsed.hostname
                        self.user = parsed.username
                        self.password = parsed.password
                        self.database = parsed.path[1:] if parsed.path else 'railway'
                        self.port = parsed.port or 3306
                    else:
                        # Handle direct connection string format
                        # Format: mysql://user:password@host:port/database
                        parts = mysql_url.replace('mysql://', '').split('@')
                        if len(parts) == 2:
                            user_pass = parts[0].split(':')
                            host_port_db = parts[1].split('/')
                            host_port = host_port_db[0].split(':')
                            
                            self.user = user_pass[0]
                            self.password = user_pass[1] if len(user_pass) > 1 else ''
                            self.host = host_port[0]
                            self.port = int(host_port[1]) if len(host_port) > 1 else 3306
                            self.database = host_port_db[1] if len(host_port_db) > 1 else 'railway'
                except Exception as e:
                    print(f"Error parsing MYSQL_URL: {e}")
        
        # Fallback to individual variables (for local development)
        if not self.host:
            self.host = os.getenv('DB_HOST', 'localhost')
        if not self.user:
            self.user = os.getenv('DB_USER', 'root')
        if not self.password:
            self.password = os.getenv('DB_PASSWORD', '')
        if not self.database:
            self.database = os.getenv('DB_NAME', 'vit_leave_management')
        if not self.port:
            self.port = int(os.getenv('DB_PORT', 3306))
        
        # Special case for Railway internal host
        if self.host == 'railway':
            # Try to get the actual host from Railway's internal DNS
            self.host = os.getenv('MYSQLHOST', 'mysql.railway.internal')
        
        # Debug: Show connection details (mask password)
        print("\n" + "="*50)
        print("DATABASE CONNECTION DETAILS:")
        print(f"Host: {self.host}")
        print(f"User: {self.user}")
        print(f"Password: {'*' * len(self.password) if self.password else '(empty)'}")
        print(f"Database: {self.database}")
        print(f"Port: {self.port}")
        print("="*50 + "\n")
    
    def _create_connection(self):
        """Create a fresh database connection with proper timeout settings"""
        try:
            connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                charset='utf8mb4',
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                autocommit=True
            )
            
            # Test connection immediately
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            print("✓ Database connection created successfully!")
            return connection
        except pymysql.err.OperationalError as e:
            print(f"✗ Database connection failed: {e}")
            print(f"\nTroubleshooting:")
            print(f"1. Check if MySQL service is running in Railway")
            print(f"2. Trying to connect to: {self.host}:{self.port}")
            print(f"3. Error code: {e.args[0] if e.args else 'Unknown'}")
            
            # Try alternative connection method for Railway
            if 'railway' in str(self.host).lower():
                print("\nTrying alternative Railway connection...")
                try:
                    # Try with mysql.railway.internal (internal Railway DNS)
                    connection = pymysql.connect(
                        host='mysql.railway.internal',
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        port=self.port,
                        cursorclass=pymysql.cursors.DictCursor,
                        charset='utf8mb4',
                        connect_timeout=30,
                        read_timeout=30,
                        write_timeout=30,
                        autocommit=True
                    )
                    print("✓ Connected via mysql.railway.internal!")
                    return connection
                except Exception as e2:
                    print(f"✗ Alternative connection also failed: {e2}")
            
            raise
    
    def get_connection(self):
        """Get a database connection with automatic reconnection"""
        try:
            connection = self._create_connection()
            return connection
        except Exception as e:
            print(f"⚠ Connection failed, retrying in 2 seconds...")
            time.sleep(2)
            try:
                connection = self._create_connection()
                print("✅ Reconnected successfully!")
                return connection
            except Exception as e2:
                print(f"✗ Reconnection failed: {e2}")
                # Create a simple in-memory connection for emergency setup
                print("⚠ Creating emergency setup mode...")
                return self._create_emergency_connection()
    
    def _create_emergency_connection(self):
        """Create a minimal connection for emergency setup"""
        try:
            # Try to connect without specifying database first
            connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                charset='utf8mb4',
                connect_timeout=30
            )
            
            with connection.cursor() as cursor:
                # Create database if it doesn't exist
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                cursor.execute(f"USE {self.database}")
            
            return connection
        except Exception as e:
            print(f"✗ Emergency connection also failed: {e}")
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
    
    def safe_execute(self, sql, params=None):
        """Execute SQL with automatic reconnection on failure"""
        max_retries = 2
        for attempt in range(max_retries):
            connection = None
            try:
                connection = self.get_connection()
                with connection.cursor() as cursor:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    if sql.strip().upper().startswith('SELECT'):
                        result = cursor.fetchall()
                        return result
                    else:
                        connection.commit()
                        return cursor.rowcount
            except pymysql.err.OperationalError as e:
                if attempt < max_retries - 1:
                    print(f"⚠ Query failed (attempt {attempt+1}), retrying...")
                    time.sleep(1)
                    continue
                else:
                    print(f"✗ Query failed after {max_retries} attempts: {e}")
                    raise
            finally:
                if connection:
                    connection.close()
    
    def init_db(self, force=False):
        """Initialize database tables with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                connection = self.get_connection()
                with connection.cursor() as cursor:
                    print(f"Attempt {attempt+1}: Creating tables...")
                    
                    # Create ALL tables your app needs
                    tables = [
                        # Students table
                        '''
                        CREATE TABLE IF NOT EXISTS students (
                            reg_number VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            proctor_id VARCHAR(20) NOT NULL,
                            hostel_block VARCHAR(10) NOT NULL,
                            room_number VARCHAR(10) NOT NULL,
                            phone VARCHAR(15),
                            parent_phone VARCHAR(15),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        ''',
                        # Proctors table
                        '''
                        CREATE TABLE IF NOT EXISTS proctors (
                            employee_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            email VARCHAR(100),
                            department VARCHAR(100),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        ''',
                        # Leaves table
                        '''
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
                            suspicious_flag BOOLEAN DEFAULT FALSE,
                            flagged_by VARCHAR(50),
                            flag_reason TEXT,
                            flagged_at TIMESTAMP NULL,
                            verified_at TIMESTAMP NULL
                        )
                        ''',
                        # Hostel supervisors table
                        '''
                        CREATE TABLE IF NOT EXISTS hostel_supervisors (
                            supervisor_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            hostel_block VARCHAR(10) NOT NULL,
                            email VARCHAR(100),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        ''',
                        # Admins table
                        '''
                        CREATE TABLE IF NOT EXISTS admins (
                            admin_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            email VARCHAR(100),
                            role ENUM('super_admin', 'admin', 'moderator') DEFAULT 'admin',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        ''',
                        # Verification logs table
                        '''
                        CREATE TABLE IF NOT EXISTS verification_logs (
                            log_id INT AUTO_INCREMENT PRIMARY KEY,
                            leave_id INT,
                            supervisor_id VARCHAR(20),
                            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            action ENUM('granted', 'rejected', 'suspicious', 'flagged') NOT NULL,
                            notes TEXT
                        )
                        ''',
                        # Admin logs table
                        '''
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
                        ''',
                        # Admin leave flags table
                        '''
                        CREATE TABLE IF NOT EXISTS admin_leave_flags (
                            flag_id INT AUTO_INCREMENT PRIMARY KEY,
                            leave_id INT NOT NULL,
                            flagged_by VARCHAR(50) NOT NULL,
                            reason TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        ''',
                        # Parent contacts table
                        '''
                        CREATE TABLE IF NOT EXISTS parent_contacts (
                            contact_id INT AUTO_INCREMENT PRIMARY KEY,
                            leave_id INT NOT NULL,
                            contact_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            method VARCHAR(50),
                            confirmation_code VARCHAR(100),
                            notes TEXT
                        )
                        ''',
                        # Leave audit log table
                        '''
                        CREATE TABLE IF NOT EXISTS leave_audit_log (
                            log_id INT AUTO_INCREMENT PRIMARY KEY,
                            leave_id INT NOT NULL,
                            action VARCHAR(50) NOT NULL,
                            performed_by VARCHAR(100) NOT NULL,
                            performed_by_type VARCHAR(50) NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            notes TEXT
                        )
                        '''
                    ]
                    
                    table_names = [
                        'students', 'proctors', 'leaves', 'hostel_supervisors',
                        'admins', 'verification_logs', 'admin_logs', 
                        'admin_leave_flags', 'parent_contacts', 'leave_audit_log'
                    ]
                    
                    for i, sql in enumerate(tables):
                        try:
                            cursor.execute(sql)
                            print(f"✓ Table '{table_names[i]}' ready")
                        except Exception as e:
                            print(f"⚠ Table '{table_names[i]}' error: {e}")
                    
                    connection.commit()
                    print("\n" + "="*50)
                    print("✅ ALL TABLES READY!")
                    print("="*50 + "\n")
                    return True
                    
            except Exception as e:
                print(f"✗ Attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    print(f"⚠ Continuing without tables...")
                    return False
            finally:
                if 'connection' in locals():
                    connection.close()