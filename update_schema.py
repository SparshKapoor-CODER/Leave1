# [file name]: update_schema.py
import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

class SchemaUpdater:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'vit_leave_management')
        self.port = int(os.getenv('DB_PORT', 3306))
        
    def get_connection(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
    
    def update_schema(self):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                print("Updating database schema...")
                
                # Add missing columns to leaves table
                columns_to_add = [
                    ("suspicious_flag", "BOOLEAN DEFAULT FALSE"),
                    ("flagged_by", "VARCHAR(50)"),
                    ("flag_reason", "TEXT"),
                    ("flagged_at", "TIMESTAMP NULL")
                ]
                
                for column_name, column_type in columns_to_add:
                    try:
                        # Check if column exists
                        cursor.execute(f"""
                            SELECT COUNT(*) as count 
                            FROM information_schema.COLUMNS 
                            WHERE TABLE_SCHEMA = '{self.database}' 
                            AND TABLE_NAME = 'leaves' 
                            AND COLUMN_NAME = '{column_name}'
                        """)
                        
                        result = cursor.fetchone()
                        if result['count'] == 0:
                            cursor.execute(f"""
                                ALTER TABLE leaves 
                                ADD COLUMN {column_name} {column_type}
                            """)
                            print(f"✓ Added column '{column_name}' to 'leaves' table")
                        else:
                            print(f"✓ Column '{column_name}' already exists")
                    
                    except Exception as e:
                        print(f"✗ Error adding column '{column_name}': {e}")
                
                # Add missing tables if they don't exist
                tables_to_create = {
                    'admins': '''
                        CREATE TABLE IF NOT EXISTS admins (
                            admin_id VARCHAR(20) PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            email VARCHAR(100),
                            role ENUM('super_admin', 'admin', 'moderator') DEFAULT 'admin',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''',
                    'admin_logs': '''
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
                    'verification_logs': '''
                        CREATE TABLE IF NOT EXISTS verification_logs (
                            log_id INT AUTO_INCREMENT PRIMARY KEY,
                            leave_id INT,
                            supervisor_id VARCHAR(20),
                            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            action ENUM('granted', 'rejected', 'suspicious', 'flagged') NOT NULL,
                            notes TEXT
                        )
                    '''
                }
                
                for table_name, create_sql in tables_to_create.items():
                    try:
                        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                        if not cursor.fetchone():
                            cursor.execute(create_sql)
                            print(f"✓ Created '{table_name}' table")
                        else:
                            print(f"✓ Table '{table_name}' already exists")
                    except Exception as e:
                        print(f"✗ Error creating table '{table_name}': {e}")
                
                connection.commit()
                print("\n" + "="*50)
                print("DATABASE SCHEMA UPDATED SUCCESSFULLY!")
                print("="*50 + "\n")
                
        except Exception as e:
            print(f"✗ Error updating schema: {e}")
            raise
        finally:
            connection.close()

if __name__ == '__main__':
    updater = SchemaUpdater()
    updater.update_schema()
    
    # Test the schema
    connection = updater.get_connection()
    try:
        with connection.cursor() as cursor:
            # Check leaves table structure
            cursor.execute("DESCRIBE leaves")
            columns = cursor.fetchall()
            print("Leaves table structure:")
            for col in columns:
                print(f"  {col['Field']}: {col['Type']}")
            
            # Check suspicious_flag column
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'leaves' 
                AND COLUMN_NAME = 'suspicious_flag'
            """, (updater.database,))
            
            result = cursor.fetchone()
            if result['count'] > 0:
                print("\n✓ 'suspicious_flag' column exists and should work now!")
            else:
                print("\n✗ 'suspicious_flag' column still missing!")
    finally:
        connection.close()