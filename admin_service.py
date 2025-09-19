"""
Admin Service Module
Handles admin authentication, dashboard, and management operations
"""
import bcrypt
import mysql.connector
from tkinter import messagebox

class InvalidDepartmentSelectionError(Exception):
    pass

class AdminService:
    def __init__(self, database_service):
        self.db = database_service

    def authenticate_admin(self, username, password):
        """Authenticate admin user"""
        try:
            admin_record = self.db.get_admin_by_username(username)
            if admin_record:
                stored_password = admin_record[2]  # password is at index 2
                if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                    return True, "Login successful"
                else:
                    return False, "Invalid password"
            else:
                return False, "Admin not found"
        except Exception as e:
            return False, f"Authentication error: {str(e)}"

    def add_new_admin(self, username, password):
        """Add new admin user"""
        if not username or not password:
            return False, "Please fill all fields."
        
        try:
            self.db.add_admin(username, password)
            return True, "New admin added successfully."
        except mysql.connector.IntegrityError:
            return False, "Username already exists."
        except Exception as e:
            return False, f"Error adding admin: {str(e)}"

    def change_admin_password(self, current_username, current_password, new_password):
        """Change admin password"""
        if not new_password:
            return False, "Please enter a new password."
        
        # Verify current credentials
        is_authenticated, message = self.authenticate_admin(current_username, current_password)
        if not is_authenticated:
            return False, "Current password is incorrect."
        
        try:
            self.db.update_admin_password(current_username, new_password)
            return True, "Password changed successfully."
        except Exception as e:
            return False, f"Error changing password: {str(e)}"

    def get_dashboard_data(self):
        """Get dashboard data including total employees, attendance rate, and department data"""
        try:
            total_employees = self.db.get_total_employees()
            attendance_rate = self.db.get_attendance_rate()
            attendance_by_department = self.db.get_attendance_by_department()

            attendance_data = [
                (dept, attendance_count, (attendance_count / employee_count) * 100 if employee_count > 0 else 0)
                for dept, employee_count, attendance_count in attendance_by_department
            ]
            return total_employees, attendance_rate, attendance_data
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return 0, 0, []

    def get_all_departments(self):
        """Get all active departments"""
        return self.db.get_all_departments()

    def register_employee(self, emp_id, emp_name, emp_department, emp_designation, face_encoding):
        """Register new employee"""
        if not emp_id or not emp_name or not emp_department or not emp_designation:
            return False, "Please fill all the fields."
        
        try:
            emp_dept_id = self.db.get_department_id_by_name(emp_department)
            if emp_dept_id is None:
                return False, "Invalid department selected."
            
            encoding_data = face_encoding.tobytes()
            self.db.add_employee(emp_id, emp_name, emp_dept_id, emp_designation, encoding_data)
            return True, "Employee registered successfully."
        except mysql.connector.IntegrityError:
            return False, "Employee ID already exists."
        except Exception as e:
            return False, f"Error registering employee: {str(e)}"

    def validate_department_selection(self, selected_department):
        """Validate if the selected department is valid"""
        if selected_department == "Select Department" or not selected_department:
            raise InvalidDepartmentSelectionError("Please select a valid department.")
        
        departments = self.get_all_departments()
        if selected_department not in departments:
            raise InvalidDepartmentSelectionError("Invalid department selected.")
        
        return True