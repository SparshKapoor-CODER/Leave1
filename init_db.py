# [file name]: init_db.py
import sys
sys.path.append('.')
from database import Database
from models import create_sample_data

def init_database():
    print("="*60)
    print("INITIALIZING DATABASE")
    print("="*60)
    
    try:
        # Create database and tables
        db = Database()
        db.init_db()
        print("✓ Database tables created successfully!")
        
        # Create sample data
        create_sample_data()
        print("✓ Sample data created successfully!")
        
        # Test connection
        connection = db.get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM students")
            student_count = cursor.fetchone()['count']
            print(f"✓ Found {student_count} students in database")
        
        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    init_database()