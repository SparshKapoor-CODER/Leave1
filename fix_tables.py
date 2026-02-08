# fix_tables.py
import pymysql
import os

def create_missing_tables():
    print("Creating missing tables for VIT Leave Management System...")
    
    # Get connection from environment (Railway provides these)
    conn = pymysql.connect(
        host=os.getenv('MYSQLHOST', 'mysql.railway.internal'),
        user=os.getenv('MYSQLUSER', 'root'),
        password=os.getenv('MYSQLPASSWORD'),
        database=os.getenv('MYSQLDATABASE', 'railway'),
        port=int(os.getenv('MYSQLPORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            tables = [
                ("""
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
                """, "admin_logs"),
                
                ("""
                CREATE TABLE IF NOT EXISTS admin_leave_flags (
                    flag_id INT AUTO_INCREMENT PRIMARY KEY,
                    leave_id INT NOT NULL,
                    flagged_by VARCHAR(50) NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """, "admin_leave_flags"),
                
                ("""
                CREATE TABLE IF NOT EXISTS parent_contacts (
                    contact_id INT AUTO_INCREMENT PRIMARY KEY,
                    leave_id INT NOT NULL,
                    contact_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    method VARCHAR(50),
                    confirmation_code VARCHAR(100),
                    notes TEXT
                )
                """, "parent_contacts"),
                
                ("""
                CREATE TABLE IF NOT EXISTS leave_audit_log (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    leave_id INT NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    performed_by VARCHAR(100) NOT NULL,
                    performed_by_type VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
                """, "leave_audit_log")
            ]
            
            for sql, table_name in tables:
                try:
                    cursor.execute(sql)
                    print(f"✅ Created/verified '{table_name}' table")
                except Exception as e:
                    print(f"⚠ Error creating '{table_name}': {e}")
            
            conn.commit()
            print("\n" + "="*60)
            print("✅ ALL MISSING TABLES CREATED SUCCESSFULLY!")
            print("="*60)
            
    finally:
        conn.close()

if __name__ == "__main__":
    create_missing_tables()