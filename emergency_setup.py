# emergency_setup.py
import os
import sys
import pymysql
import bcrypt

print("="*70)
print("🚨 VIT LEAVE MANAGEMENT SYSTEM - EMERGENCY SETUP")
print("="*70)

# Get environment variables
def get_env_var(var_name, default=None):
    value = os.getenv(var_name)
    if not value and default is not None:
        value = default
    print(f"{var_name}: {value if var_name != 'MYSQLPASSWORD' else '********'}")
    return value

# Get connection details
host = get_env_var('MYSQLHOST', 'mysql.railway.internal')
user = get_env_var('MYSQLUSER', 'root')
password = get_env_var('MYSQLPASSWORD', '')
database = get_env_var('MYSQLDATABASE', 'railway')
port = int(get_env_var('MYSQLPORT', '3306'))

# Also try MYSQL_URL
mysql_url = os.getenv('MYSQL_URL')
if mysql_url:
    print(f"MYSQL_URL: {mysql_url}")
    # Try to parse it
    if 'mysql://' in mysql_url:
        parts = mysql_url.replace('mysql://', '').split('@')
        if len(parts) == 2:
            user_pass = parts[0].split(':')
            host_port_db = parts[1].split('/')
            host_port = host_port_db[0].split(':')
            
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else password
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else port
            database = host_port_db[1] if len(host_port_db) > 1 else database

print("\n" + "="*70)
print("FINAL CONNECTION DETAILS:")
print(f"Host: {host}")
print(f"User: {user}")
print(f"Database: {database}")
print(f"Port: {port}")
print("="*70)

try:
    # Try to connect
    print("\n🔄 Connecting to database...")
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        charset='utf8mb4',
        connect_timeout=30
    )
    
    with connection.cursor() as cursor:
        print("✅ Connected to MySQL server!")
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE {database}")
        print(f"✅ Using database: {database}")
        
        # Create basic tables
        print("\n🔄 Creating tables...")
        
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
                parent_phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created 'students' table")
        
        # Create proctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proctors (
                employee_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                department VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created 'proctors' table")
        
        # Create admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                role VARCHAR(50) DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created 'admins' table")
        
        # Create hostel_supervisors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hostel_supervisors (
                supervisor_id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                hostel_block VARCHAR(10) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created 'hostel_supervisors' table")
        
        # Create leaves table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaves (
                leave_id INT AUTO_INCREMENT PRIMARY KEY,
                student_reg VARCHAR(20) NOT NULL,
                proctor_id VARCHAR(20) NOT NULL,
                leave_type VARCHAR(50) NOT NULL,
                from_date DATE NOT NULL,
                to_date DATE NOT NULL,
                from_time TIME NOT NULL,
                to_time TIME NOT NULL,
                reason TEXT NOT NULL,
                destination VARCHAR(200),
                parent_contacted BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'pending',
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP NULL,
                qr_token VARCHAR(100),
                qr_expiry TIMESTAMP NULL,
                verified_at TIMESTAMP NULL,
                suspicious_flag BOOLEAN DEFAULT FALSE
            )
        ''')
        print("✓ Created 'leaves' table")
        
        # Create default admin user
        print("\n🔄 Creating default admin user...")
        admin_password = "Admin@123"
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT IGNORE INTO admins (admin_id, name, password_hash, email, role)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('ADMIN001', 'System Administrator', hashed_password, 'admin@vit.ac.in', 'super_admin'))
        print("✅ Created admin: ADMIN001 / Admin@123")
        
        # Create default proctor
        proctor_password = "Proctor@123"
        hashed_proctor_password = bcrypt.hashpw(proctor_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT IGNORE INTO proctors (employee_id, name, password_hash, email, department)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('P001', 'Dr. Rajit Nair', hashed_proctor_password, 'rajit.nair@vit.ac.in', 'CSE'))
        print("✅ Created proctor: P001 / Proctor@123")
        
        # Create default student
        student_password = "Student@123"
        hashed_student_password = bcrypt.hashpw(student_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT IGNORE INTO students 
            (reg_number, name, password_hash, proctor_id, hostel_block, room_number, phone, parent_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', ('24BAI10017', 'Test Student', hashed_student_password, 'P001', 'A Block', '101', '9876543210', '9876543211'))
        print("✅ Created student: 24BAI10017 / Student@123")
        
        # Create default supervisor
        supervisor_password = "Supervisor@123"
        hashed_supervisor_password = bcrypt.hashpw(supervisor_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT IGNORE INTO hostel_supervisors 
            (supervisor_id, name, password_hash, hostel_block, email)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('S001', 'Mr. Kumar', hashed_supervisor_password, 'A Block', 'kumar@vit.ac.in'))
        print("✅ Created supervisor: S001 / Supervisor@123")
        
        connection.commit()
        
    print("\n" + "="*70)
    print("🎉 EMERGENCY SETUP COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n📋 DEFAULT LOGIN CREDENTIALS:")
    print("-" * 40)
    print("🔐 ADMIN: ADMIN001 / Admin@123")
    print("👨‍🏫 PROCTOR: P001 / Proctor@123")
    print("👨‍🎓 STUDENT: 24BAI10017 / Student@123")
    print("🏠 SUPERVISOR: S001 / Supervisor@123")
    print("\n🌐 Login URL: https://leave1-production.up.railway.app")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*70)
    print("TROUBLESHOOTING:")
    print("1. Check if MySQL service is running in Railway")
    print("2. Verify your MYSQL_URL or MYSQLHOST environment variables")
    print("3. Try connecting manually with: mysql -h [host] -u [user] -p")
    print("="*70)
finally:
    if 'connection' in locals():
        connection.close()

if __name__ == '__main__':
    pass