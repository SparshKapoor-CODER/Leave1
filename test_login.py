from models import Student, Proctor, HostelSupervisor
import sys

def test_login():
    print("Testing student login...")
    
    # Test your credentials
    student = Student.login("24BAI10017", "Sparsh123")
    if student:
        print(f"✓ Student login successful!")
        print(f"  Name: {student['name']}")
        print(f"  Reg: {student['reg_number']}")
        print(f"  Proctor ID: {student['proctor_id']}")
    else:
        print("✗ Student login failed!")
        print("Possible reasons:")
        print("1. Registration number not in database")
        print("2. Password mismatch")
        print("3. Database connection issue")
    
    print("\nTesting proctor login...")
    proctor = Proctor.login("P001", "proctor123")
    if proctor:
        print(f"✓ Proctor login successful!")
        print(f"  Name: {proctor['name']}")
    else:
        print("✗ Proctor login failed!")
    
    print("\nTesting hostel supervisor login...")
    supervisor = HostelSupervisor.login("S001", "supervisor123")
    if supervisor:
        print(f"✓ Hostel supervisor login successful!")
        print(f"  Name: {supervisor['name']}")
    else:
        print("✗ Hostel supervisor login failed!")

if __name__ == '__main__':
    test_login()