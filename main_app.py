"""
Main Application File
Biometric Attendance System - Microservices Architecture
This file orchestrates all the services and provides the GUI interface
"""
import tkinter as tk
import os
import sys
import cv2
import numpy as np
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import our microservices
from database_service import DatabaseService
from face_recognition_service import FaceRecognitionService
from admin_service import AdminService, InvalidDepartmentSelectionError
from attendance_service import AttendanceService

class BiometricAttendanceApp:
    def __init__(self):
        # Initialize services
        self.db_service = DatabaseService()
        self.face_service = FaceRecognitionService()
        self.admin_service = AdminService(self.db_service)
        self.attendance_service = AttendanceService(self.db_service, self.face_service)
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Biometric Attendance System")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create frames
        self.setup_frames()
        self.setup_main_frame()
        self.setup_admin_login_frame()
        self.setup_attendance_frame()
        
        # Show initial frame
        self.show_frame(self.main_frame)

    def setup_frames(self):
        """Setup main container frames"""
        self.main_frame = tk.Frame(self.root)
        self.admin_login_frame = tk.Frame(self.root)
        self.admin_dashboard_frame = tk.Frame(self.root)
        self.attendance_frame = tk.Frame(self.root)
        
        for frame in (self.main_frame, self.admin_login_frame, self.admin_dashboard_frame, self.attendance_frame):
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame):
        """Show specified frame"""
        frame.tkraise()

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                self.db_service.close()
            except:
                pass
            self.root.destroy()
            sys.exit()

    def setup_main_frame(self):
        """Setup main welcome frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.main_frame, text="Biometric Attendance System", font=("Arial", 24)).pack(pady=50)
        
        btn_admin = tk.Button(self.main_frame, text="Admin Panel", font=("Arial", 16), 
                             command=lambda: self.show_frame(self.admin_login_frame))
        btn_admin.pack(pady=20)
        
        btn_attendance = tk.Button(self.main_frame, text="Mark Attendance", font=("Arial", 16),
                                  command=lambda: self.show_frame(self.attendance_frame))
        btn_attendance.pack(pady=20)

    def setup_admin_login_frame(self):
        """Setup admin login frame"""
        for widget in self.admin_login_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.admin_login_frame, text="Admin Login", font=("Arial", 20)).pack(pady=20)
        
        tk.Label(self.admin_login_frame, text="Username:").pack(pady=5)
        self.admin_username_entry = tk.Entry(self.admin_login_frame)
        self.admin_username_entry.pack(pady=5)
        
        tk.Label(self.admin_login_frame, text="Password:").pack(pady=5)
        self.admin_password_entry = tk.Entry(self.admin_login_frame, show="*")
        self.admin_password_entry.pack(pady=5)
        
        btn_login = tk.Button(self.admin_login_frame, text="Login", command=self.admin_login)
        btn_login.pack(pady=10)
        
        btn_back = tk.Button(self.admin_login_frame, text="Back", command=lambda: self.show_frame(self.main_frame))
        btn_back.pack(pady=10)

    def admin_login(self):
        """Handle admin login"""
        username = self.admin_username_entry.get()
        password = self.admin_password_entry.get()
        
        is_authenticated, message = self.admin_service.authenticate_admin(username, password)
        
        if is_authenticated:
            self.current_admin = username
            self.setup_admin_dashboard()
            self.show_frame(self.admin_dashboard_frame)
            self.admin_username_entry.delete(0, tk.END)
            self.admin_password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Login Failed", message)

    def setup_admin_dashboard(self):
        """Setup admin dashboard frame"""
        for widget in self.admin_dashboard_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.admin_dashboard_frame, text="Admin Dashboard", font=("Arial", 20)).pack(pady=20)
        
        # Dashboard data
        total_employees, attendance_rate, attendance_data = self.admin_service.get_dashboard_data()
        
        # Display dashboard info
        info_frame = tk.Frame(self.admin_dashboard_frame)
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text=f"Total Employees: {total_employees}", font=("Arial", 12)).pack()
        tk.Label(info_frame, text=f"Today's Attendance Rate: {attendance_rate:.1f}%", font=("Arial", 12)).pack()
        
        # Dashboard plot
        if attendance_data:
            self.create_dashboard_plot(attendance_data)
        
        # Admin menu buttons
        btn_frame = tk.Frame(self.admin_dashboard_frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="View Attendance", command=self.setup_view_attendance_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Register Employee", command=self.setup_registration_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Add Admin", command=self.setup_add_admin_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Change Password", command=self.setup_change_password_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Logout", command=lambda: self.show_frame(self.main_frame)).pack(side=tk.LEFT, padx=5)

    def create_dashboard_plot(self, attendance_data):
        """Create attendance dashboard plot"""
        departments = [data[0] for data in attendance_data]
        attendance_percentages = [data[2] for data in attendance_data]
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(departments, attendance_percentages)
        ax.set_ylabel('Attendance Percentage')
        ax.set_title('Department-wise Attendance Today')
        ax.set_ylim(0, 100)
        
        canvas = FigureCanvasTkAgg(fig, self.admin_dashboard_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def setup_view_attendance_frame(self):
        """Setup view attendance frame"""
        view_window = tk.Toplevel(self.root)
        view_window.title("View Attendance")
        view_window.geometry("800x600")
        
        tk.Label(view_window, text="View Attendance Records", font=("Arial", 16)).pack(pady=10)
        
        # Department selection
        tk.Label(view_window, text="Select Department:").pack()
        departments = self.admin_service.get_all_departments()
        department_var = tk.StringVar(value="Select Department")
        department_combo = ttk.Combobox(view_window, textvariable=department_var, values=departments, state="readonly")
        department_combo.pack(pady=5)
        
        # Date selection
        date_frame = tk.Frame(view_window)
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="From:").grid(row=0, column=0, padx=5)
        start_date = DateEntry(date_frame)
        start_date.grid(row=0, column=1, padx=5)
        
        tk.Label(date_frame, text="To:").grid(row=0, column=2, padx=5)
        end_date = DateEntry(date_frame)
        end_date.grid(row=0, column=3, padx=5)
        
        # Display button
        def display_attendance():
            selected_department = department_var.get()
            try:
                self.admin_service.validate_department_selection(selected_department)
                attendance_data, export_records = self.attendance_service.get_attendance_records(
                    selected_department, start_date.get(), end_date.get())
                
                # Create treeview for display
                tree = ttk.Treeview(view_window, columns=('Date', 'EmpID', 'Name', 'CheckIn', 'CheckOut', 'WorkTime'), show='headings')
                
                for col in tree['columns']:
                    tree.heading(col, text=col)
                    tree.column(col, width=100)
                
                for record in attendance_data:
                    tree.insert('', tk.END, values=record)
                
                tree.pack(fill=tk.BOTH, expand=True, pady=10)
                
                # Export button
                tk.Button(view_window, text="Export to Excel", 
                         command=lambda: self.attendance_service.export_attendance_to_excel(export_records)).pack(pady=5)
                
            except InvalidDepartmentSelectionError as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(view_window, text="Display Attendance", command=display_attendance).pack(pady=10)

    def setup_registration_frame(self):
        """Setup employee registration frame"""
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Register Employee")
        reg_window.geometry("400x500")
        
        tk.Label(reg_window, text="Employee Registration", font=("Arial", 16)).pack(pady=10)
        
        # Form fields
        tk.Label(reg_window, text="Employee ID:").pack()
        emp_id_entry = tk.Entry(reg_window)
        emp_id_entry.pack(pady=5)
        
        tk.Label(reg_window, text="Name:").pack()
        name_entry = tk.Entry(reg_window)
        name_entry.pack(pady=5)
        
        tk.Label(reg_window, text="Department:").pack()
        departments = self.admin_service.get_all_departments()
        dept_var = tk.StringVar(value="Select Department")
        dept_combo = ttk.Combobox(reg_window, textvariable=dept_var, values=departments, state="readonly")
        dept_combo.pack(pady=5)
        
        tk.Label(reg_window, text="Designation:").pack()
        designation_entry = tk.Entry(reg_window)
        designation_entry.pack(pady=5)
        
        def capture_image():
            """Capture and process employee image"""
            capture_window = tk.Toplevel(reg_window)
            capture_window.title("Capture Image")
            
            lmain = tk.Label(capture_window)
            lmain.pack()
            
            cap = cv2.VideoCapture(0)
            
            update_frame = self.face_service.create_camera_window_update_function(lmain, cap, capture_window)
            
            def capture_and_save():
                ret, frame = cap.read()
                if ret:
                    cap.release()
                    capture_window.destroy()
                    
                    face_locations, rgb_frame = self.face_service.detect_faces(frame)
                    face_encoding, error = self.face_service.encode_face(rgb_frame, face_locations)
                    
                    if error:
                        messagebox.showerror("Error", error)
                        return
                    
                    emp_id = emp_id_entry.get()
                    emp_name = name_entry.get()
                    emp_department = dept_var.get()
                    emp_designation = designation_entry.get()
                    
                    # Save face image
                    output_dir = "C:\\Users\\kumar\\Desktop\\register"
                    self.face_service.extract_and_save_face(frame, face_locations, emp_id, output_dir)
                    
                    # Register employee
                    success, message = self.admin_service.register_employee(
                        emp_id, emp_name, emp_department, emp_designation, face_encoding)
                    
                    if success:
                        messagebox.showinfo("Success", message)
                        reg_window.destroy()
                    else:
                        messagebox.showerror("Error", message)
            
            tk.Button(capture_window, text="Capture", command=capture_and_save).pack()
            
            def on_closing():
                cap.release()
                capture_window.destroy()
            
            capture_window.protocol("WM_DELETE_WINDOW", on_closing)
            update_frame()
        
        tk.Button(reg_window, text="Capture Image", command=capture_image).pack(pady=20)

    def setup_add_admin_frame(self):
        """Setup add admin frame"""
        admin_window = tk.Toplevel(self.root)
        admin_window.title("Add Admin")
        admin_window.geometry("300x200")
        
        tk.Label(admin_window, text="Add New Admin", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(admin_window, text="Username:").pack()
        username_entry = tk.Entry(admin_window)
        username_entry.pack(pady=5)
        
        tk.Label(admin_window, text="Password:").pack()
        password_entry = tk.Entry(admin_window, show="*")
        password_entry.pack(pady=5)
        
        def save_admin():
            username = username_entry.get()
            password = password_entry.get()
            
            success, message = self.admin_service.add_new_admin(username, password)
            
            if success:
                messagebox.showinfo("Success", message)
                admin_window.destroy()
            else:
                messagebox.showerror("Error", message)
        
        tk.Button(admin_window, text="Save", command=save_admin).pack(pady=10)

    def setup_change_password_frame(self):
        """Setup change password frame"""
        pwd_window = tk.Toplevel(self.root)
        pwd_window.title("Change Password")
        pwd_window.geometry("300x250")
        
        tk.Label(pwd_window, text="Change Admin Password", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(pwd_window, text="Current Password:").pack()
        current_pwd_entry = tk.Entry(pwd_window, show="*")
        current_pwd_entry.pack(pady=5)
        
        tk.Label(pwd_window, text="New Password:").pack()
        new_pwd_entry = tk.Entry(pwd_window, show="*")
        new_pwd_entry.pack(pady=5)
        
        def change_password():
            current_pwd = current_pwd_entry.get()
            new_pwd = new_pwd_entry.get()
            
            success, message = self.admin_service.change_admin_password(
                self.current_admin, current_pwd, new_pwd)
            
            if success:
                messagebox.showinfo("Success", message)
                pwd_window.destroy()
            else:
                messagebox.showerror("Error", message)
        
        tk.Button(pwd_window, text="Change Password", command=change_password).pack(pady=10)

    def setup_attendance_frame(self):
        """Setup attendance marking frame"""
        for widget in self.attendance_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.attendance_frame, text="Mark Attendance", font=("Arial", 20)).pack(pady=20)
        
        tk.Label(self.attendance_frame, text="Employee ID:").pack(pady=10)
        self.employee_id_entry = tk.Entry(self.attendance_frame)
        self.employee_id_entry.pack(pady=5)
        
        def mark_attendance(is_markin=True):
            emp_id = self.employee_id_entry.get().strip()
            success, message = self.attendance_service.mark_attendance(emp_id, is_markin)
            
            if success:
                messagebox.showinfo("Attendance", message)
            else:
                messagebox.showerror("Error", message)
            
            self.employee_id_entry.delete(0, tk.END)
        
        btn_mark_in = tk.Button(self.attendance_frame, text="Mark In", 
                               command=lambda: mark_attendance(is_markin=True))
        btn_mark_in.pack(pady=10)
        
        btn_mark_out = tk.Button(self.attendance_frame, text="Mark Out", 
                                command=lambda: mark_attendance(is_markin=False))
        btn_mark_out.pack(pady=10)
        
        btn_back = tk.Button(self.attendance_frame, text="Back to Main Screen", 
                            command=lambda: [self.employee_id_entry.delete(0, tk.END), self.show_frame(self.main_frame)])
        btn_back.pack(pady=10)

    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BiometricAttendanceApp()
    app.run()