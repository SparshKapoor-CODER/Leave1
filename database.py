import pymysql
import os
from urllib.parse import urlparse
import bcrypt

class Database:
    def __init__(self):
        # Get DATABASE_URL from environment
        db_url = os.getenv('DATABASE_URL')
        print(f"🔧 DATABASE_URL: {db_url[:50]}..." if db_url else "❌ No DATABASE_URL found")
        
        if db_url and 'mysql://' in db_url:
            # Parse DATABASE_URL
            parsed = urlparse(db_url)
            self.host = parsed.hostname
            self.user = parsed.username
            self.password = parsed.password
            self.database = parsed.path[1:] if parsed.path.startswith('/') else parsed.path
            self.port = parsed.port or 3306
            print(f"✅ Parsed from DATABASE_URL: {self.user}@{self.host}:{self.port}/{self.database}")
        else:
            # Use individual variables
            self.host = os.getenv('DB_HOST', 'localhost')
            self.user = os.getenv('DB_USER', 'root')
            self.password = os.getenv('DB_PASSWORD', '')
            self.database = os.getenv('DB_NAME', 'railway')
            self.port = int(os.getenv('DB_PORT', 3306))
            print(f"⚠️ Using individual variables: {self.user}@{self.host}:{self.port}/{self.database}")
    
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
                connect_timeout=5
            )
            print(f"✅ Database connected to {self.host}:{self.port}")
            return connection
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)[:100]}")
            # Don't raise - let app continue
            return None
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def check_password(hashed_password, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except:
            return False
    
    def init_db(self):
        try:
            conn = self.get_connection()
            if not conn:
                print("⚠️ Skipping database initialization - no connection")
                return False
            
            with conn.cursor() as cursor:
                cursor.execute(f"USE {self.database}")
                print(f"✅ Using database: {self.database}")
                
                # Just check if tables exist
                cursor.execute("SHOW TABLES LIKE 'admins'")
                if cursor.fetchone():
                    print("✅ Found existing tables")
                else:
                    print("⚠️ No tables found - app will work but database features limited")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️ Database init warning: {str(e)[:100]}")
            return False
