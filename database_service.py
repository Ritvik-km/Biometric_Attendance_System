"""
Database Service Module
Handles all database operations for the Biometric Attendance System
"""
import mysql.connector
import os
from dotenv import load_dotenv
import bcrypt

class DatabaseService:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv("host")
        self.user = os.getenv("user")
        self.password = os.getenv("password")
        self.database = os.getenv("database")
        self.conn = None
        self.cursor = None
        self.connect()
        self.initialize_tables()

    def connect(self):
        """Establish database connection"""
        self.conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor()

    def initialize_tables(self):
        """Create necessary tables if they don't exist"""
        # Create admins table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) UNIQUE,
                password VARCHAR(255)
            )
        ''')
        
        # Check if default admin exists, if not create one
        self.cursor.execute("SELECT * FROM admins")
        if self.cursor.fetchone() is None:
            hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            self.cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", ('admin', hashed_password))
            self.conn.commit()

    def get_admin_by_username(self, username):
        """Get admin by username"""
        self.cursor.execute("SELECT * FROM admins WHERE username=%s", (username,))
        return self.cursor.fetchone()

    def add_admin(self, username, password):
        """Add new admin"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (username, hashed_password))
        self.conn.commit()

    def update_admin_password(self, username, new_password):
        """Update admin password"""
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        self.cursor.execute("UPDATE admins SET password=%s WHERE username=%s", (hashed_password, username))
        self.conn.commit()

    def get_employee_by_id(self, emp_id):
        """Get employee by ID"""
        self.cursor.execute("SELECT em_employee_name, em_employee_face_encoding FROM employee_master WHERE em_employee_id=%s", (emp_id,))
        return self.cursor.fetchone()

    def add_employee(self, emp_id, emp_name, emp_dept_id, emp_designation, face_encoding):
        """Add new employee"""
        self.cursor.execute("""
            INSERT INTO employee_master 
            (em_employee_id, em_employee_name, em_employee_dept, em_employee_designation, em_employee_face_encoding, em_employee_active) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_id, emp_name, emp_dept_id, emp_designation, face_encoding, 1))
        self.conn.commit()

    def get_department_id_by_name(self, dept_name):
        """Get department ID by name"""
        self.cursor.execute("SELECT dm_dept_id FROM department_master WHERE dm_dept_desc=%s", (dept_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_all_departments(self):
        """Get all active departments"""
        self.cursor.execute("SELECT dm_dept_desc FROM department_master WHERE dm_dept_active = 1")
        return [row[0] for row in self.cursor.fetchall()]

    def get_total_employees(self):
        """Get total number of active employees"""
        self.cursor.execute("SELECT COUNT(*) FROM employee_master WHERE em_employee_active = 1")
        return self.cursor.fetchone()[0]

    def get_attendance_rate(self):
        """Get today's attendance rate"""
        self.cursor.execute(""" 
            SELECT 
                (SELECT COUNT(DISTINCT et_employee_id) 
                FROM employee_transactions 
                WHERE DATE(et_employee_in_time) = CURRENT_DATE) / 
                (SELECT COUNT(*) 
                FROM employee_master 
                WHERE em_employee_active = 1) * 100 AS attendance_rate;
        """)
        result = self.cursor.fetchone()[0]
        return result or 0

    def get_attendance_by_department(self):
        """Get attendance data by department"""
        self.cursor.execute(""" 
            SELECT 
                dm.dm_dept_desc AS department_desc,
                COUNT(em.em_employee_id) AS employee_count,
                COUNT(DISTINCT et.et_employee_id) AS attendance_count
            FROM 
                department_master dm
            LEFT JOIN 
                employee_master em ON dm.dm_dept_id = em.em_employee_dept AND em.em_employee_active = 1
            LEFT JOIN 
                employee_transactions et ON em.em_employee_id = et.et_employee_id 
                AND DATE(et.et_employee_in_time) = CURRENT_DATE
            WHERE 
                dm.dm_dept_active = 1
            GROUP BY 
                dm.dm_dept_desc;
        """)
        return self.cursor.fetchall()

    def check_attendance_exists(self, emp_id, date_today):
        """Check if attendance already exists for employee today"""
        self.cursor.execute("""
            SELECT * FROM employee_transactions
            WHERE et_employee_id=%s AND DATE(et_employee_in_time)=%s AND DATE(et_employee_out_time)=%s
        """, (emp_id, date_today, date_today))
        return self.cursor.fetchone()

    def add_attendance_in(self, emp_id, timestamp, image_path):
        """Add check-in attendance"""
        self.cursor.execute("""
            INSERT INTO employee_transactions (et_employee_id, et_employee_in_time, et_employee_in_imgpth) 
            VALUES (%s, %s, %s)
        """, (emp_id, timestamp, image_path))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_attendance_out(self, emp_id, timestamp, image_path, date_today):
        """Update check-out attendance"""
        self.cursor.execute("""
            UPDATE employee_transactions 
            SET et_employee_out_time=%s, et_employee_out_imgpth=%s, et_worktime = TIMEDIFF(et_employee_out_time, et_employee_in_time) 
            WHERE et_employee_id=%s AND DATE(et_employee_in_time)=%s AND et_employee_out_time IS NULL
        """, (timestamp, image_path, emp_id, date_today))
        self.conn.commit()

    def get_attendance_records(self, department, start_datetime, end_datetime):
        """Get attendance records for a department within date range"""
        self.cursor.execute('''
            SELECT DATE(et.et_employee_in_time), et.et_employee_id, em.em_employee_name, et.et_employee_in_time, et.et_employee_out_time, et.et_worktime
            FROM employee_transactions et
            JOIN employee_master em ON et.et_employee_id = em.em_employee_id
            JOIN department_master d ON em.em_employee_dept = d.dm_dept_id
            WHERE d.dm_dept_desc = %s AND et.et_employee_in_time >= %s AND et.et_employee_in_time < %s;
        ''', (department, start_datetime, end_datetime))
        return self.cursor.fetchall()

    def get_daily_attendance_records(self, department, single_date):
        """Get daily attendance records for a department"""
        self.cursor.execute('''
            SELECT et.et_employee_id, em.em_employee_name, et.et_employee_in_time, et.et_employee_out_time, et.et_worktime
            FROM employee_transactions et
            JOIN employee_master em ON et.et_employee_id = em.em_employee_id
            JOIN department_master d ON em.em_employee_dept = d.dm_dept_id
            WHERE d.dm_dept_desc = %s AND DATE(et.et_employee_in_time) = %s;
        ''', (department, single_date))
        return self.cursor.fetchall()

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()