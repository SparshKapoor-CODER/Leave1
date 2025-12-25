# [file name]: test_admin_features.py
import sys
sys.path.append('.')
from models import AdminModel

def test_admin_features():
    print("="*60)
    print("TESTING ADMIN FEATURES")
    print("="*60)
    
    # Test 1: Add a new proctor
    print("\n1. Testing Add Proctor...")
    proctor_data = {
        'employee_id': 'P008',
        'name': 'Abhinav Kumar',
        'password': 'Abhinav@123',
        'email': 'abhinav.kumar@vitbhopal.ac.in',
        'department': 'SASL'
    }
    result = AdminModel.add_proctor(proctor_data)
    print(f"   Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    
    # Test 2: Add a new student
    print("\n2. Testing Add Student...")
    student_data = {
        'reg_number': '25BCE1001',
        'name': 'Test Student',
        'password': 'Student@123',
        'proctor_id': 'P001',
        'hostel_block': 'B',
        'room_number': '101',
        'phone': '9876543210',
        'parent_phone': '9876543211'
    }
    result = AdminModel.add_student(student_data)
    print(f"   Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    
    # Test 3: Add a new supervisor
    print("\n3. Testing Add Supervisor...")
    supervisor_data = {
        'supervisor_id': 'S003',
        'name': 'Test Supervisor',
        'password': 'Supervisor@123',
        'hostel_block': 'C',
        'email': 'test.supervisor@vit.ac.in'
    }
    result = AdminModel.add_supervisor(supervisor_data)
    print(f"   Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    
    # Test 4: Get user details
    print("\n4. Testing Get User...")
    user = AdminModel.get_user('student', '25BCE1001')
    print(f"   Result: {'✓ FOUND' if user else '✗ NOT FOUND'}")
    if user:
        print(f"   Name: {user['name']}")
    
    # Test 5: Update student
    print("\n5. Testing Update Student...")
    update_data = {
        'name': 'Updated Test Student',
        'proctor_id': 'P001',
        'hostel_block': 'C',
        'room_number': '202',
        'phone': '9876543222',
        'parent_phone': '9876543223'
    }
    result = AdminModel.update_student('25BCE1001', update_data)
    print(f"   Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    
    # Test 6: Reset password
    print("\n6. Testing Reset Password...")
    result = AdminModel.reset_password('student', '25BCE1001', 'NewPassword123')
    print(f"   Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    
    # Test 7: Get all users
    print("\n7. Testing Get All Users...")
    users = AdminModel.get_all_users()
    print(f"   Result: Found {len(users)} users")
    
    # Test 8: Get system stats
    print("\n8. Testing Get System Stats...")
    stats = AdminModel.get_system_stats()
    print(f"   Result: {stats}")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED!")
    print("="*60)

if __name__ == '__main__':
    test_admin_features()