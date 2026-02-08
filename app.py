# [file name]: app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta, time
import secrets
from models import Student, Proctor, HostelSupervisor, AdminModel
from database import Database
import os
from dotenv import load_dotenv
import functools
import traceback
from pdf_generator import PDFGenerator, ReportData
import base64

load_dotenv('.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

print("\n" + "="*60)
print("VIT LEAVE MANAGEMENT SYSTEM - STARTING...")
print("="*60)

# ==============================================
# FIXED DATABASE INITIALIZATION
# ==============================================
try:
    print("🔄 Initializing database...")
    db = Database()
    
    # Force create tables
    print("🔄 Creating database tables...")
    db.init_db(force=True)  # Force create all tables
    
    print("✅ Database tables created successfully!")
    
    # Now check and create admin
    connection = db.get_connection()
    try:
        with connection.cursor() as cursor:
            # Check if admins table exists and has any admins
            cursor.execute("""
                SELECT COUNT(*) as admin_count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'admins'
            """)
            table_exists = cursor.fetchone()['admin_count'] > 0
            
            if not table_exists:
                print("⚠ Admins table doesn't exist yet. Creating it...")
                # Re-run init_db to ensure tables are created
                db.init_db()
            
            # Check for admin users
            cursor.execute("SELECT COUNT(*) as count FROM admins")
            admin_count = cursor.fetchone()['count']
            
            if admin_count == 0:
                print("\n" + "="*60)
                print("⚠ NO ADMIN FOUND - CREATING DEFAULT ADMIN USER...")
                print("="*60)
                
                from models import UserModel
                admin_password = UserModel.hash_password("Admin@123")
                
                cursor.execute("""
                    INSERT INTO admins (admin_id, name, password_hash, email, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("ADMIN001", "System Administrator", admin_password, "admin@vit.ac.in", "super_admin"))
                
                connection.commit()
                
                print("\n" + "="*60)
                print("✅ DEFAULT ADMIN CREATED SUCCESSFULLY!")
                print("   Username: ADMIN001")
                print("   Password: Admin@123")
                print("="*60)
                
                # Also create a proctor for testing
                proctor_password = UserModel.hash_password("Proctor@123")
                cursor.execute("""
                    INSERT IGNORE INTO proctors 
                    (employee_id, name, password_hash, email, department)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("P001", "Dr. Rajit Nair", proctor_password, "rajit.nair@vit.ac.in", "CSE"))
                
                # Create a test student
                student_password = UserModel.hash_password("Student@123")
                cursor.execute("""
                    INSERT IGNORE INTO students 
                    (reg_number, name, password_hash, proctor_id, hostel_block, room_number, phone, parent_phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, ("24BAI10017", "Test Student", student_password, "P001", "A Block", "101", "9876543210", "9876543211"))
                
                # Create a hostel supervisor
                supervisor_password = UserModel.hash_password("Supervisor@123")
                cursor.execute("""
                    INSERT IGNORE INTO hostel_supervisors 
                    (supervisor_id, name, password_hash, hostel_block, email)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("S001", "Mr. Kumar", supervisor_password, "A Block", "kumar@vit.ac.in"))
                
                connection.commit()
                print("\n✅ Test users created for immediate testing!")
                print("   Proctor: P001 / Proctor@123")
                print("   Student: 24BAI10017 / Student@123")
                print("   Supervisor: S001 / Supervisor@123")
                print("="*60 + "\n")
            else:
                print(f"✅ Found {admin_count} existing admin(s)")
                
    except Exception as e:
        print(f"✗ Error checking/creating admin: {e}")
        traceback.print_exc()
        
        # Emergency fallback - create admin directly
        try:
            from models import UserModel
            admin_password = UserModel.hash_password("Admin@123")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    role VARCHAR(50) DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT IGNORE INTO admins (admin_id, name, password_hash, email, role)
                VALUES (%s, %s, %s, %s, %s)
            """, ("ADMIN001", "System Administrator", admin_password, "admin@vit.ac.in", "super_admin"))
            
            connection.commit()
            print("⚠ Emergency admin created due to error!")
        except Exception as e2:
            print(f"✗ Even emergency creation failed: {e2}")
    finally:
        connection.close()
        
except Exception as e:
    print(f"✗ Database initialization failed: {e}")
    traceback.print_exc()
    print("⚠ Continuing in limited mode...")

# ==============================================
# SIMPLIFIED SETUP ROUTE (NO TOKEN REQUIRED)
# ==============================================
@app.route('/setup/initialize-system', methods=['GET', 'POST'])
def initialize_system():
    """Emergency endpoint to initialize system with default users"""
    from models import UserModel
    
    db = Database()
    
    if request.method == 'POST':
        try:
            connection = db.get_connection()
            cursor = connection.cursor()
            
            print("🔄 Running emergency system initialization...")
            
            # Step 1: Create tables if they don't exist
            print("🔄 Creating database tables...")
            try:
                # Create basic tables first
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        admin_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        role VARCHAR(50) DEFAULT 'admin',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS proctors (
                        employee_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        department VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        reg_number VARCHAR(20) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        proctor_id VARCHAR(50),
                        hostel_block VARCHAR(50),
                        room_number VARCHAR(20),
                        phone VARCHAR(20),
                        parent_phone VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (proctor_id) REFERENCES proctors(employee_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hostel_supervisors (
                        supervisor_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        hostel_block VARCHAR(50),
                        email VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leaves (
                        leave_id INT AUTO_INCREMENT PRIMARY KEY,
                        student_reg VARCHAR(20),
                        leave_type VARCHAR(50),
                        from_date DATE,
                        to_date DATE,
                        from_time TIME,
                        to_time TIME,
                        reason TEXT,
                        destination VARCHAR(200),
                        parent_contacted BOOLEAN DEFAULT FALSE,
                        status VARCHAR(20) DEFAULT 'pending',
                        proctor_id VARCHAR(50),
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        approved_at TIMESTAMP NULL,
                        approved_by VARCHAR(50),
                        qr_token VARCHAR(100),
                        qr_generated_at TIMESTAMP NULL,
                        qr_expiry TIMESTAMP NULL,
                        verified_at TIMESTAMP NULL,
                        verified_by VARCHAR(50),
                        suspicious_flag BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (student_reg) REFERENCES students(reg_number),
                        FOREIGN KEY (proctor_id) REFERENCES proctors(employee_id)
                    )
                """)
                
                print("✅ Basic tables created!")
            except Exception as e:
                print(f"⚠ Table creation error (may already exist): {e}")
            
            # Step 2: Create admin user
            cursor.execute("SELECT COUNT(*) as count FROM admins")
            admin_count = cursor.fetchone()['count']
            
            if admin_count == 0:
                admin_hash = UserModel.hash_password("Admin@123")
                cursor.execute("""
                    INSERT INTO admins (admin_id, name, password_hash, email, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("ADMIN001", "System Administrator", admin_hash, "admin@vit.ac.in", "super_admin"))
                print("✅ Admin created: ADMIN001 / Admin@123")
            
            # Step 3: Create proctor user
            cursor.execute("SELECT COUNT(*) as count FROM proctors WHERE employee_id = 'P001'")
            proctor_count = cursor.fetchone()['count']
            
            if proctor_count == 0:
                proctor_hash = UserModel.hash_password("Proctor@123")
                cursor.execute("""
                    INSERT INTO proctors (employee_id, name, password_hash, email, department)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("P001", "Dr. Rajit Nair", proctor_hash, "rajit.nair@vit.ac.in", "CSE"))
                print("✅ Proctor created: P001 / Proctor@123")
            
            # Step 4: Create student user
            cursor.execute("SELECT COUNT(*) as count FROM students WHERE reg_number = '24BAI10017'")
            student_count = cursor.fetchone()['count']
            
            if student_count == 0:
                student_hash = UserModel.hash_password("Student@123")
                cursor.execute("""
                    INSERT INTO students 
                    (reg_number, name, password_hash, proctor_id, hostel_block, room_number, phone, parent_phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, ("24BAI10017", "Test Student", student_hash, "P001", "A Block", "101", "9876543210", "9876543211"))
                print("✅ Student created: 24BAI10017 / Student@123")
            
            # Step 5: Create supervisor user
            cursor.execute("SELECT COUNT(*) as count FROM hostel_supervisors WHERE supervisor_id = 'S001'")
            supervisor_count = cursor.fetchone()['count']
            
            if supervisor_count == 0:
                supervisor_hash = UserModel.hash_password("Supervisor@123")
                cursor.execute("""
                    INSERT INTO hostel_supervisors 
                    (supervisor_id, name, password_hash, hostel_block, email)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("S001", "Mr. Kumar", supervisor_hash, "A Block", "kumar@vit.ac.in"))
                print("✅ Supervisor created: S001 / Supervisor@123")
            
            connection.commit()
            connection.close()
            
            return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>✅ System Initialized!</title>
                    <style>
                        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                        .success { background: #d4edda; color: #155724; padding: 20px; border-radius: 5px; }
                        .credentials { background: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #007bff; }
                        a { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
                        a:hover { background: #0056b3; }
                    </style>
                </head>
                <body>
                    <div class="success">
                        <h1>✅ System Initialized Successfully!</h1>
                        <p>Default users have been created. You can now log in.</p>
                    </div>
                    
                    <div class="credentials">
                        <h3>Default Login Credentials:</h3>
                        <p><strong>Admin:</strong> ADMIN001 / Admin@123</p>
                        <p><strong>Proctor:</strong> P001 / Proctor@123</p>
                        <p><strong>Student:</strong> 24BAI10017 / Student@123</p>
                        <p><strong>Supervisor:</strong> S001 / Supervisor@123</p>
                    </div>
                    
                    <a href="/admin/login">Go to Admin Login</a><br><br>
                    <a href="/">Go to Home Page</a>
                </body>
                </html>
            '''
        
        except Exception as e:
            return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>❌ Setup Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }}
                        pre {{ background: #f8f9fa; padding: 10px; overflow-x: auto; }}
                        a {{ display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="error">
                        <h1>❌ Setup Failed</h1>
                        <p>Error: {str(e)}</p>
                        <h3>Debug Information:</h3>
                        <pre>{traceback.format_exc()}</pre>
                    </div>
                    <a href="/">Go Back</a>
                </body>
                </html>
            '''
    
    # Show setup form (GET request)
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>🔧 System Setup</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .warning { background: #fff3cd; color: #856404; padding: 20px; border-radius: 5px; margin: 20px 0; }
                button { background: #28a745; color: white; border: none; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #218838; }
                .note { background: #f8f9fa; padding: 15px; margin: 20px 0; border-left: 4px solid #17a2b8; }
            </style>
        </head>
        <body>
            <h1>🔧 VIT Leave Management System - Initial Setup</h1>
            
            <div class="warning">
                <h3>⚠ Attention</h3>
                <p>This will create all necessary database tables and default users.</p>
                <p><strong>Only run this if:</strong></p>
                <ul>
                    <li>This is the first time setting up the system</li>
                    <li>Database tables are missing</li>
                    <li>You cannot log in with any user</li>
                </ul>
            </div>
            
            <div class="note">
                <h3>📝 What will be created:</h3>
                <ul>
                    <li>All necessary database tables</li>
                    <li>Admin user: ADMIN001 / Admin@123</li>
                    <li>Proctor user: P001 / Proctor@123</li>
                    <li>Student user: 24BAI10017 / Student@123</li>
                    <li>Supervisor user: S001 / Supervisor@123</li>
                </ul>
            </div>
            
            <form method="POST" onsubmit="this.querySelector('button').innerHTML = 'Initializing... Please wait...'; this.querySelector('button').disabled = true;">
                <p><strong>Click the button below to initialize the system:</strong></p>
                <button type="submit">🚀 Initialize System Now</button>
            </form>
            
            <p><em>Note: This process may take 10-20 seconds. Do not close the browser.</em></p>
        </body>
        </html>
    '''

# ==============================================
# REST OF THE APP.PY CODE CONTINUES HERE...
# ==============================================

def login_required(role):
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if role not in session:
                if role == 'student_id':
                    return redirect(url_for('student_login'))
                elif role == 'proctor_id':
                    return redirect(url_for('proctor_login'))
                elif role == 'supervisor_id':
                    return redirect(url_for('hostel_login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        reg_number = request.form['reg_number'].strip().upper()
        password = request.form['password']
        
        print(f"Student login attempt: {reg_number}")
        
        student = Student.login(reg_number, password)
        if student:
            session['student_id'] = student['reg_number']
            session['student_name'] = student['name']
            flash(f'Welcome back, {student["name"]}!', 'success')
            return redirect(url_for('student_dashboard'))
        
        flash('Invalid registration number or password', 'error')
        return render_template('student_login.html', error='Invalid credentials')
    
    return render_template('student_login.html')

@app.route('/student/dashboard')
@login_required('student_id')
def student_dashboard():
    leaves = Student.get_leave_history(session['student_id'])
    return render_template('student_dashboard.html', 
                         leaves=leaves, 
                         student_name=session['student_name'],
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/student/apply', methods=['GET', 'POST'])
@login_required('student_id')
def apply_leave():
    if request.method == 'POST':
        try:
            leave_data = {
                'leave_type': request.form['leave_type'],
                'from_date': request.form['from_date'],
                'to_date': request.form['to_date'],
                'from_time': request.form['from_time'],
                'to_time': request.form['to_time'],
                'reason': request.form['reason'],
                'destination': request.form.get('destination', ''),
                'parent_contacted': 'parent_contacted' in request.form
            }
            
            from_date = datetime.strptime(leave_data['from_date'], '%Y-%m-%d')
            to_date = datetime.strptime(leave_data['to_date'], '%Y-%m-%d')
            
            if from_date > to_date:
                flash('Invalid date range!', 'error')
                return render_template('apply_leave.html', 
                                     today=datetime.now().strftime('%Y-%m-%d'))
            
            leave_id = Student.apply_leave(session['student_id'], leave_data)
            if leave_id:
                flash('Leave application submitted successfully!', 'success')
            else:
                flash('Failed to apply for leave', 'error')
                
        except Exception as e:
            print(f"Error applying leave: {e}")
            traceback.print_exc()
            flash(f'Error: {str(e)}', 'error')
            
    return render_template('apply_leave.html', 
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/proctor/login', methods=['GET', 'POST'])
def proctor_login():
    if request.method == 'POST':
        employee_id = request.form['employee_id'].strip()
        password = request.form['password']
        
        proctor = Proctor.login(employee_id, password)
        if proctor:
            session['proctor_id'] = proctor['employee_id']
            session['proctor_name'] = proctor['name']
            flash(f'Welcome, Dr. {proctor["name"]}!', 'success')
            return redirect(url_for('proctor_dashboard'))
        
        flash('Invalid employee ID or password', 'error')
        return render_template('proctor_login.html', error='Invalid credentials')
    
    return render_template('proctor_login.html')

@app.route('/proctor/dashboard')
@login_required('proctor_id')
def proctor_dashboard():
    pending_leaves = Proctor.get_pending_leaves(session['proctor_id'])
    return render_template('proctor_dashboard.html', 
                         leaves=pending_leaves, 
                         proctor_name=session['proctor_name'])

@app.route('/proctor/approve/<int:leave_id>')
@login_required('proctor_id')
def approve_leave(leave_id):
    try:
        qr_token = Proctor.approve_leave(leave_id, session['proctor_id'])
        if qr_token:
            flash('Leave approved successfully! QR code generated.', 'success')
        else:
            flash('Error approving leave', 'error')
    except Exception as e:
        print(f"Error approving leave: {e}")
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('proctor_dashboard'))

@app.route('/proctor/reject/<int:leave_id>')
@login_required('proctor_id')
def reject_leave(leave_id):
    try:
        success = Proctor.reject_leave(leave_id, session['proctor_id'])
        if success:
            flash('Leave rejected successfully.', 'info')
        else:
            flash('Error rejecting leave', 'error')
    except Exception as e:
        print(f"Error rejecting leave: {e}")
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('proctor_dashboard'))

@app.route('/hostel/login', methods=['GET', 'POST'])
def hostel_login():
    if request.method == 'POST':
        supervisor_id = request.form['supervisor_id'].strip()
        password = request.form['password']
        
        supervisor = HostelSupervisor.login(supervisor_id, password)
        if supervisor:
            session['supervisor_id'] = supervisor['supervisor_id']
            session['supervisor_name'] = supervisor['name']
            session['hostel_block'] = supervisor['hostel_block']
            flash(f'Welcome, {supervisor["name"]}!', 'success')
            return redirect(url_for('hostel_verify'))
        
        flash('Invalid supervisor ID or password', 'error')
        return render_template('hostel_login.html', error='Invalid credentials')
    
    return render_template('hostel_login.html')

@app.route('/hostel/verify', methods=['GET', 'POST'])
@login_required('supervisor_id')
def hostel_verify():
    error = None
    success = None
    slip = None
    
    if 'slip_data' in session:
        slip = session.pop('slip_data', None)
        success = "Verification successful!"
    
    if request.method == 'POST':
        qr_token = request.form.get('qr_token', '').strip().upper()
        
        if not qr_token:
            error = 'Please enter QR code'
            flash(error, 'error')
            return render_template('hostel_verify.html',
                                 supervisor_name=session.get('supervisor_name', ''),
                                 hostel_block=session.get('hostel_block', ''),
                                 error=error)
        
        print(f"Verifying QR token: {qr_token}")
        
        try:
            # Get supervisor's block from session
            supervisor_block = session.get('hostel_block', '')
            
            leave, message = HostelSupervisor.verify_qr_token(
                qr_token, 
                session['supervisor_id'],
                supervisor_block  # Pass supervisor's block for verification
            )
            
            if leave:
                # Additional verification: Check if student's block matches supervisor's block
                student_block = leave.get('hostel_block', '')
                
                if student_block.upper() != supervisor_block.upper():
                    error = f"Access denied! You can only verify students from Block {supervisor_block}. This student is from Block {student_block}."
                    flash(error, 'error')
                    return render_template('hostel_verify.html',
                                         supervisor_name=session.get('supervisor_name', ''),
                                         hostel_block=session.get('hostel_block', ''),
                                         error=error)
                
                # Rest of the code remains the same...
                def format_time(time_obj):
                    if isinstance(time_obj, time):
                        return time_obj.strftime('%H:%M')
                    elif isinstance(time_obj, timedelta):
                        total_seconds = int(time_obj.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        return f"{hours:02d}:{minutes:02d}"
                    elif isinstance(time_obj, str):
                        if ':' in time_obj:
                            return time_obj.split('.')[0]
                        return time_obj
                    else:
                        return "00:00"
                
                def format_date(date_obj):
                    if hasattr(date_obj, 'strftime'):
                        return date_obj.strftime('%Y-%m-%d')
                    elif isinstance(date_obj, str):
                        return date_obj
                    else:
                        return str(date_obj)
                
                from_date = format_date(leave['from_date'])
                to_date = format_date(leave['to_date'])
                from_time = format_time(leave['from_time'])
                to_time = format_time(leave['to_time'])
                
                slip_data = {
                    'student_name': leave.get('student_name', 'Unknown'),
                    'reg_number': leave.get('student_reg', 'Unknown'),
                    'hostel_block': leave.get('hostel_block', 'Unknown'),
                    'room_number': leave.get('room_number', 'Unknown'),
                    'from_date': from_date,
                    'to_date': to_date,
                    'from_time': from_time,
                    'to_time': to_time,
                    'proctor_name': leave.get('proctor_name', 'Unknown'),
                    'verified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'supervisor_name': session.get('supervisor_name', 'Supervisor'),
                    'destination': leave.get('destination', 'Not specified')
                }
                
                session['slip_data'] = slip_data
                session.modified = True
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        'success': True,
                        'message': message,
                        'slip': slip_data,
                        'redirect': url_for('hostel_verify')
                    })
                
                success = message
                slip = slip_data
                flash(success, 'success')
            else:
                error = message
                flash(error, 'error')
                
        except Exception as e:
            error = f"Server error: {str(e)}"
            print(f"Error in hostel_verify: {e}")
            traceback.print_exc()
            flash(error, 'error')
    
    return render_template('hostel_verify.html',
                         supervisor_name=session.get('supervisor_name', ''),
                         hostel_block=session.get('hostel_block', ''),
                         slip=slip,
                         error=error,
                         success=success)

@app.route('/hostel/verify/clear')
@login_required('supervisor_id')
def clear_verification():
    if 'slip_data' in session:
        session.pop('slip_data', None)
    return redirect(url_for('hostel_verify'))

@app.route('/api/generate_qr/<int:leave_id>')
@login_required('student_id')
def generate_qr(leave_id):
    try:
        leaves = Student.get_leave_history(session['student_id'])
        target_leave = None
        for leave in leaves:
            if leave['leave_id'] == leave_id and leave['status'] == 'approved':
                target_leave = leave
                break
        
        if not target_leave or not target_leave['qr_token']:
            return jsonify({'error': 'No valid QR code available'}), 404
        
        qr_image = HostelSupervisor.generate_qr_code(target_leave['qr_token'])
        
        return jsonify({
            'qr_image': qr_image,
            'leave_id': leave_id,
            'valid_until': target_leave['qr_expiry'].strftime('%Y-%m-%d %H:%M:%S') if target_leave['qr_expiry'] else None
        })
    except Exception as e:
        print(f"Error generating QR code: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form['admin_id'].strip().upper()
        password = request.form['password']
        
        admin = AdminModel.login(admin_id, password)
        if admin:
            session['admin_id'] = admin['admin_id']
            session['admin_name'] = admin['name']
            session['admin_role'] = admin['role']
            
            # Log admin login
            AdminModel.log_action(
                admin_id=admin['admin_id'],
                action_type='LOGIN',
                target_type='SYSTEM',
                target_id=None,
                details='Admin logged into system',
                request=request
            )
            
            flash(f'Welcome, {admin["name"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid admin ID or password', 'error')
        return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        stats = AdminModel.get_system_stats()
        recent_logs = AdminModel.get_all_logs(limit=20)
        suspicious_leaves = AdminModel.get_all_leaves({'suspicious_only': True})
        
        return render_template('admin_dashboard.html',
                            stats=stats,
                            recent_logs=recent_logs,
                            suspicious_leaves=suspicious_leaves,
                            admin_name=session['admin_name'],
                            admin_role=session['admin_role'])
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        # Return simple dashboard without complex queries
        return render_template('admin_simple_dashboard.html',
                            error=str(e),
                            admin_name=session['admin_name'])

@app.route('/admin/leaves')
@admin_required
def admin_leaves():
    filters = {
        'status': request.args.get('status'),
        'leave_type': request.args.get('leave_type'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'suspicious_only': request.args.get('suspicious_only') == 'true'
    }
    
    leaves = AdminModel.get_all_leaves(filters)
    return render_template('admin_leaves.html',
                         leaves=leaves,
                         filters=filters,
                         admin_name=session['admin_name'])

@app.route('/admin/logs')
@admin_required
def admin_logs():
    logs = AdminModel.get_all_logs(limit=200)
    return render_template('admin_logs.html',
                         logs=logs,
                         admin_name=session['admin_name'])

@app.route('/admin/users')
@admin_required
def admin_users():
    users = AdminModel.get_all_users()
    db = Database()
    connection = db.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT employee_id, name FROM proctors ORDER BY name")
            proctors = cursor.fetchall()
    finally:
        connection.close()
    
    return render_template('admin_users.html',
                         users=users,
                         proctors=proctors,
                         admin_name=session['admin_name'])

@app.route('/admin/add-user', methods=['POST'])
@admin_required
def admin_add_user():
    user_type = request.form['user_type']
    
    # DEBUG: Print all form data
    print(f"\n{'='*50}")
    print(f"ADD USER REQUEST - Type: {user_type}")
    print(f"Form data: {dict(request.form)}")
    print(f"{'='*50}\n")
    
    try:
        if user_type == 'proctor':
            proctor_data = {
                'employee_id': request.form['employee_id'].strip(),
                'name': request.form['name'].strip(),
                'password': request.form['password'],
                'email': request.form['email'].strip(),
                'department': request.form['department'].strip()
            }
            
            # Validate required fields
            if not all([proctor_data['employee_id'], proctor_data['name'], proctor_data['password']]):
                flash('Please fill all required fields for proctor', 'error')
                return redirect(url_for('admin_users'))
            
            # Call the AdminModel method
            success = AdminModel.add_proctor(proctor_data)
            if success:
                # Log the action
                AdminModel.log_action(
                    admin_id=session['admin_id'],
                    action_type='ADD_USER',
                    target_type='PROCTOR',
                    target_id=proctor_data['employee_id'],
                    details=f'Added proctor: {proctor_data["name"]} ({proctor_data["employee_id"]})',
                    request=request
                )
                flash(f'Proctor {proctor_data["employee_id"]} added successfully!', 'success')
            else:
                flash(f'Failed to add proctor {proctor_data["employee_id"]}', 'error')
            
        elif user_type == 'student':
            student_data = {
                'reg_number': request.form['reg_number'].strip().upper(),
                'name': request.form['name'].strip(),
                'password': request.form['password'],
                'proctor_id': request.form['proctor_id'].strip(),
                'hostel_block': request.form['hostel_block'].strip(),
                'room_number': request.form['room_number'].strip(),
                'phone': request.form['phone'].strip(),
                'parent_phone': request.form['parent_phone'].strip()
            }
            
            # Validate required fields
            required_fields = ['reg_number', 'name', 'password', 'proctor_id', 'hostel_block', 'room_number']
            missing_fields = [field for field in required_fields if not student_data.get(field)]
            
            if missing_fields:
                flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
                return redirect(url_for('admin_users'))
            
            # Call the AdminModel method
            success = AdminModel.add_student(student_data)
            if success:
                # Log the action
                AdminModel.log_action(
                    admin_id=session['admin_id'],
                    action_type='ADD_USER',
                    target_type='STUDENT',
                    target_id=student_data['reg_number'],
                    details=f'Added student: {student_data["name"]} ({student_data["reg_number"]})',
                    request=request
                )
                flash(f'Student {student_data["reg_number"]} added successfully!', 'success')
            else:
                flash(f'Failed to add student {student_data["reg_number"]}', 'error')
            
        elif user_type == 'supervisor':
            supervisor_data = {
                'supervisor_id': request.form['supervisor_id'].strip(),
                'name': request.form['name'].strip(),
                'password': request.form['password'],
                'hostel_block': request.form['hostel_block'].strip(),
                'email': request.form['email'].strip()
            }
            
            # Validate required fields
            if not all([supervisor_data['supervisor_id'], supervisor_data['name'], 
                       supervisor_data['password'], supervisor_data['hostel_block']]):
                flash('Please fill all required fields for supervisor', 'error')
                return redirect(url_for('admin_users'))
            
            # Call the AdminModel method
            success = AdminModel.add_supervisor(supervisor_data)
            if success:
                # Log the action
                AdminModel.log_action(
                    admin_id=session['admin_id'],
                    action_type='ADD_USER',
                    target_type='SUPERVISOR',
                    target_id=supervisor_data['supervisor_id'],
                    details=f'Added supervisor: {supervisor_data["name"]} ({supervisor_data["supervisor_id"]})',
                    request=request
                )
                flash(f'Supervisor {supervisor_data["supervisor_id"]} added successfully!', 'success')
            else:
                flash(f'Failed to add supervisor {supervisor_data["supervisor_id"]}', 'error')
        
        else:
            flash('Invalid user type', 'error')
            return redirect(url_for('admin_users'))
        
    except Exception as e:
        flash(f'Error adding user: {str(e)}', 'error')
        print(f"Error in admin_add_user: {e}")
        traceback.print_exc()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/edit-user', methods=['POST'])
@admin_required
def admin_edit_user():
    user_type = request.form.get('user_type')
    
    try:
        if user_type == 'proctor':
            update_data = {
                'name': request.form['name'],
                'email': request.form['email'],
                'department': request.form['department']
            }
            if 'password' in request.form and request.form['password']:
                update_data['password'] = request.form['password']
            
            success = AdminModel.update_proctor(request.form['employee_id'], update_data)
            if success:
                # Log the action
                AdminModel.log_action(
                    admin_id=session['admin_id'],
                    action_type='EDIT_USER',
                    target_type='PROCTOR',
                    target_id=request.form['employee_id'],
                    details=f'Updated proctor details',
                    request=request
                )
                flash('Proctor updated successfully!', 'success')
            else:
                flash('Failed to update proctor', 'error')
            
        elif user_type == 'student':
            update_data = {
                'name': request.form['name'],
                'proctor_id': request.form['proctor_id'],
                'hostel_block': request.form['hostel_block'],
                'room_number': request.form['room_number'],
                'phone': request.form['phone'],
                'parent_phone': request.form['parent_phone']
            }
            if 'password' in request.form and request.form['password']:
                update_data['password'] = request.form['password']
            
            success = AdminModel.update_student(request.form['reg_number'], update_data)
            if success:
                # Log the action
                AdminModel.log_action(
                    admin_id=session['admin_id'],
                    action_type='EDIT_USER',
                    target_type='STUDENT',
                    target_id=request.form['reg_number'],
                    details=f'Updated student details',
                    request=request
                )
                flash('Student updated successfully!', 'success')
            else:
                flash('Failed to update student', 'error')
            
        elif user_type == 'supervisor':
            update_data = {
                'name': request.form['name'],
                'hostel_block': request.form['hostel_block'],
                'email': request.form['email']
            }
            if 'password' in request.form and request.form['password']:
                update_data['password'] = request.form['password']
            
            success = AdminModel.update_supervisor(request.form['supervisor_id'], update_data)
            if success:
                # Log the action
                AdminModel.log_action(
                    admin_id=session['admin_id'],
                    action_type='EDIT_USER',
                    target_type='SUPERVISOR',
                    target_id=request.form['supervisor_id'],
                    details=f'Updated supervisor details',
                    request=request
                )
                flash('Supervisor updated successfully!', 'success')
            else:
                flash('Failed to update supervisor', 'error')
        
        else:
            flash('Invalid user type', 'error')
            return redirect(url_for('admin_users'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/get-user/<user_type>/<user_id>')
@admin_required
def admin_get_user(user_type, user_id):
    try:
        user = AdminModel.get_user(user_type, user_id)
        if user:
            return jsonify({
                'success': True,
                'user': user,
                'user_type': user_type
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/reset-password', methods=['POST'])
@admin_required
def admin_reset_password():
    user_type = request.form['user_type']
    user_id = request.form['user_id']
    new_password = request.form['new_password']
    
    success = AdminModel.reset_password(user_type, user_id, new_password)
    if success:
        # Log the action
        AdminModel.log_action(
            admin_id=session['admin_id'],
            action_type='RESET_PASSWORD',
            target_type=user_type.upper(),
            target_id=user_id,
            details='Password reset by admin',
            request=request
        )
        flash(f'Password reset successfully for {user_id}', 'success')
    else:
        flash('Failed to reset password', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/flag-suspicious/<int:leave_id>', methods=['POST'])
@admin_required
def admin_flag_suspicious(leave_id):
    reason = request.form['reason']
    
    success = AdminModel.flag_suspicious(leave_id, session['admin_id'], reason)
    if success:
        # Log the action
        AdminModel.log_action(
            admin_id=session['admin_id'],
            action_type='FLAG_LEAVE',
            target_type='LEAVE',
            target_id=leave_id,
            details=f'Flagged as suspicious: {reason}',
            request=request
        )
        flash('Leave flagged as suspicious', 'success')
    else:
        flash('Failed to flag leave', 'error')
    
    return redirect(request.referrer or url_for('admin_leaves'))

@app.route('/admin/remove-flag/<int:leave_id>')
@admin_required
def admin_remove_flag(leave_id):
    success = AdminModel.remove_flag(leave_id)
    if success:
        # Log the action
        AdminModel.log_action(
            admin_id=session['admin_id'],
            action_type='REMOVE_FLAG',
            target_type='LEAVE',
            target_id=leave_id,
            details='Removed suspicious flag',
            request=request
        )
        flash('Suspicious flag removed', 'success')
    else:
        flash('Failed to remove flag', 'error')
    
    return redirect(request.referrer or url_for('admin_leaves'))

@app.route('/admin/delete-user', methods=['POST'])
@admin_required
def admin_delete_user():
    user_type = request.form['user_type']
    user_id = request.form['user_id']
    
    db = Database()
    connection = db.get_connection()
    try:
        with connection.cursor() as cursor:
            table_map = {
                'student': ('students', 'reg_number'),
                'proctor': ('proctors', 'employee_id'),
                'supervisor': ('hostel_supervisors', 'supervisor_id'),
                'admin': ('admins', 'admin_id')
            }
            
            if user_type not in table_map:
                flash('Invalid user type', 'error')
                return redirect(url_for('admin_users'))
            
            table_name, id_column = table_map[user_type]
            
            if user_type == 'proctor':
                cursor.execute("SELECT COUNT(*) as count FROM students WHERE proctor_id = %s", (user_id,))
                student_count = cursor.fetchone()['count']
                if student_count > 0:
                    flash(f'Cannot delete proctor with {student_count} assigned students', 'error')
                    return redirect(url_for('admin_users'))
            
            cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = %s", (user_id,))
            connection.commit()
            
            # Log the action
            AdminModel.log_action(
                admin_id=session['admin_id'],
                action_type='DELETE_USER',
                target_type=user_type.upper(),
                target_id=user_id,
                details=f'Deleted {user_type} from system',
                request=request
            )
            
            flash(f'{user_type.capitalize()} deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        connection.close()
    
    return redirect(url_for('admin_users'))

@app.route('/admin/logout')
def admin_logout():
    # Log the action before clearing session
    if 'admin_id' in session:
        AdminModel.log_action(
            admin_id=session['admin_id'],
            action_type='LOGOUT',
            target_type='SYSTEM',
            target_id=None,
            details='Admin logged out',
            request=request
        )
    
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('admin_role', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/logout/<role>')
def logout(role):
    # Log admin logout if applicable
    if role == 'admin' and 'admin_id' in session:
        AdminModel.log_action(
            admin_id=session['admin_id'],
            action_type='LOGOUT',
            target_type='SYSTEM',
            target_id=None,
            details='Admin logged out via logout route',
            request=request
        )
    
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/test/verification')
def test_verification():
    try:
        db = Database()
        connection = db.get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT qr_token FROM leaves WHERE qr_token IS NOT NULL LIMIT 1")
            result = cursor.fetchone()
        
        if result:
            qr_token = result['qr_token']
            return f"""
                <h1>Test Verification</h1>
                <p>Sample QR Token: {qr_token}</p>
                <form method="POST" action="/hostel/verify">
                    <input type="hidden" name="qr_token" value="{qr_token}">
                    <button type="submit">Test Verify</button>
                </form>
                <p><a href="/hostel/verify">Back to verification</a></p>
            """
        else:
            return "<h1>No test QR tokens available</h1>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

@app.route('/test')
def test():
    return {
        'status': 'online',
        'database': 'vit_leave_management',
        'message': 'VIT Leave Management System is running',
        'session_data': dict(session) if session else {}
    }

@app.route('/clear')
def clear_session():
    session.clear()
    return "Session cleared!"

@app.route('/setup/sample-data')
def setup_sample_data():
    """Manual endpoint to create sample data - only run when needed"""
    from models import create_sample_data
    try:
        create_sample_data()
        flash('Sample data created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating sample data: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Remove the old test routes and keep only the new simple setup route

@app.route('/debug/user-form', methods=['POST'])
def debug_user_form():
    """Debug endpoint to see what form data is being sent"""
    print("\n" + "="*60)
    print("DEBUG USER FORM DATA")
    print(f"Request method: {request.method}")
    print(f"Form data: {dict(request.form)}")
    print(f"Headers: {dict(request.headers)}")
    print("="*60 + "\n")
    
    return jsonify({
        'success': True,
        'form_data': dict(request.form),
        'message': 'Form data received'
    })

# ... [Rest of the existing routes continue here, but I'll truncate for brevity]
# The rest of your app.py routes remain the same from the original file

# Add this at the end to ensure the app runs
if __name__ == '__main__':
    print("\n" + "="*60)
    print("SYSTEM STARTED SUCCESSFULLY!")
    print("="*60)
    print("\nEMERGENCY SETUP URL:")
    print("  https://leave1-production.up.railway.app/setup/initialize-system")
    print("\nDefault Credentials (after setup):")
    print("  Admin: ADMIN001 / Admin@123")
    print("  Proctor: P001 / Proctor@123")
    print("  Student: 24BAI10017 / Student@123")
    print("  Supervisor: S001 / Supervisor@123")
    print("\n" + "="*60)
    app.run(debug=True, port=5000)