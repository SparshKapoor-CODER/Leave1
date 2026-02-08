# setup_first_deploy.py
import sys
sys.path.append('.')
from database import Database
from models import UserModel

def setup_initial_data():
    print("\n" + "="*70)
    print("VIT LEAVE MANAGEMENT SYSTEM - FIRST TIME SETUP")
    print("="*70)
    
    db = Database()
    connection = None
    
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        
        # 1. Create Admin
        admin_password = UserModel.hash_password("Admin@123")
        cursor.execute("""
            INSERT IGNORE INTO admins (admin_id, name, password_hash, email, role)
            VALUES (%s, %s, %s, %s, %s)
        """, ("ADMIN001", "System Administrator", admin_password, "admin@vit.ac.in", "super_admin"))
        
        # 2. Create Proctor
        proctor_password = UserModel.hash_password("Proctor@123")
        cursor.execute("""
            INSERT IGNORE INTO proctors 
            (employee_id, name, password_hash, email, department)
            VALUES (%s, %s, %s, %s, %s)
        """, ("P001", "Dr. Rajit Nair", proctor_password, "rajit.nair@vit.ac.in", "CSE"))
        
        # 3. Create Student
        student_password = UserModel.hash_password("Student@123")
        cursor.execute("""
            INSERT IGNORE INTO students 
            (reg_number, name, password_hash, proctor_id, hostel_block, room_number, phone, parent_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ("24BAI10017", "Test Student", student_password, "P001", "A Block", "101", "9876543210", "9876543211"))
        
        # 4. Create Hostel Supervisor
        supervisor_password = UserModel.hash_password("Supervisor@123")
        cursor.execute("""
            INSERT IGNORE INTO hostel_supervisors 
            (supervisor_id, name, password_hash, hostel_block, email)
            VALUES (%s, %s, %s, %s, %s)
        """, ("S001", "Mr. Kumar", supervisor_password, "A Block", "kumar@vit.ac.in"))
        
        # 5. Create Additional Test Data
        for i in range(1, 4):
            cursor.execute("""
                INSERT IGNORE INTO students 
                (reg_number, name, password_hash, proctor_id, hostel_block, room_number)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                f"22BCE100{i}", 
                f"Student {i}", 
                UserModel.hash_password("Test@123"), 
                "P001", 
                "B Block", 
                f"20{i}"
            ))
        
        connection.commit()
        
        print("\n✅ FIRST-TIME SETUP COMPLETE!")
        print("="*70)
        print("\nDEFAULT LOGIN CREDENTIALS:")
        print("-" * 40)
        print("🔐 ADMIN:")
        print("   Username: ADMIN001")
        print("   Password: Admin@123")
        print("\n👨‍🏫 PROCTOR:")
        print("   Username: P001")
        print("   Password: Proctor@123")
        print("\n👨‍🎓 STUDENT:")
        print("   Username: 24BAI10017")
        print("   Password: Student@123")
        print("\n🏠 HOSTEL SUPERVISOR:")
        print("   Username: S001")
        print("   Password: Supervisor@123")
        print("\n🌐 Application URL:")
        print("   https://leave1-production.up.railway.app")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    setup_initial_data()