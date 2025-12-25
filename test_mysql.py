import pymysql
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

print("Testing database connection...")
print(f"User: {os.getenv('DB_USER')}")
print(f"Password: {'*' * len(os.getenv('DB_PASSWORD', ''))}")

try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'vit_leave_management'),
        port=int(os.getenv('DB_PORT', 3306))
    )
    print("✓ Connected to MySQL!")
    
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
    
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")