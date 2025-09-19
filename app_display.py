import tkinter as tk
import os
import sys
from tkinter import messagebox, ttk
import cv2
import face_recognition
import mysql.connector
import numpy as np
from PIL import Image, ImageTk
from tkcalendar import DateEntry
from datetime import datetime
from datetime import timedelta
import bcrypt
import pandas as pd
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dotenv import load_dotenv

from refactored_project import database

load_dotenv()

host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
database = os.getenv("database")

conn = mysql.connector.connect(
    host=host,      
    user=user,  
    password=password, 
    database=database    
)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(255) UNIQUE,
        password VARCHAR(255)
    )
''')

c.execute("SELECT * FROM admins")
if c.fetchone() is None:
    hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
    c.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", ('admin', hashed_password))
    conn.commit()


def on_closing():
    
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        try:
            c.close()
            conn.close()    
        except:
            pass          
        root.destroy()
        sys.exit()

root = tk.Tk()
root.title("Attendance System")

is_admin_logged_in = False

main_frame = tk.Frame(root)

attendance_frame = tk.Frame(root)

admin_login_frame = tk.Frame(root)
admin_dashboard_frame = tk.Frame(root)

view_employees_frame = tk.Frame(root)
view_attendance_frame = tk.Frame(root)
open_registration_frame = tk.Frame(root)
add_admin_frame = tk.Frame(root)
change_admin_password_frame = tk.Frame(root)

for frame in (main_frame, attendance_frame, admin_login_frame, admin_dashboard_frame, view_employees_frame, view_attendance_frame,
              open_registration_frame, add_admin_frame, change_admin_password_frame):
    frame.grid(row=0, column=0, sticky='nsew')

root.protocol("WM_DELETE_WINDOW", on_closing)

def show_frame(frame):
    frame.tkraise()

def setup_main_frame():
    img_path = "C:\\Users\\kumar\\Documents\\Programming\\Python\\Project\\Banner.png"
    logo_image = Image.open(img_path)
    logo_image = ImageTk.PhotoImage(logo_image)

    main_frame.logo_img = logo_image
    tk.Label(main_frame, image=main_frame.logo_img).pack(fill="both", expand=True, pady=10)

    tk.Label(main_frame, text="Welcome to the Attendance System", font=("Arial", 20)).pack(pady=5)

    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=20) 

    btn_admin_login = tk.Button(button_frame, text="Admin Login", relief="raised", command=lambda: show_frame(admin_login_frame))
    btn_admin_login.pack(side="left", padx=20) 

    btn_open_attendance = tk.Button(button_frame, text="Open Attendance", command=lambda: show_frame(attendance_frame))
    btn_open_attendance.pack(side="left", padx=20) 


def setup_admin_login_frame():
    tk.Label(admin_login_frame, text="Admin Login", font=("Arial", 16)).pack(pady=20)
    
    tk.Label(admin_login_frame, text="Username").pack()
    entry_username = tk.Entry(admin_login_frame)
    entry_username.pack()
    
    tk.Label(admin_login_frame, text="Password").pack()
    entry_password = tk.Entry(admin_login_frame, show="*")
    entry_password.pack()
    
    def verify_admin():
        username = entry_username.get()
        password = entry_password.get()
        
        if username == '' or password == '':
            messagebox.showerror("Error", "Please fill all fields.")
            return
        
        c.execute("SELECT password FROM admins WHERE username=%s", (username,))
        record = c.fetchone()
        if record and bcrypt.checkpw(password.encode('utf-8'), record[0].encode('utf-8')):
            global is_admin_logged_in
            is_admin_logged_in = True
            show_frame(admin_dashboard_frame)
            setup_admin_dashboard()
            entry_username.delete(0, tk.END)
            entry_password.delete(0, tk.END) 
        else:
            messagebox.showerror("Error", "Invalid credentials.")

    btn_login = tk.Button(admin_login_frame, text="Login", command=verify_admin)
    btn_login.pack(pady=10)

    btn_back_home = tk.Button(admin_login_frame, text="Back to Main Screen", command=lambda: show_frame(main_frame))
    btn_back_home.pack(pady=10)


def setup_admin_dashboard():   
    for widget in admin_dashboard_frame.winfo_children():
        widget.destroy()
    
    tk.Label(admin_dashboard_frame, text="Admin Dashboard", font=("Arial", 20)).pack(pady=20)

    def fetch_daily_data():
        try:
            c.execute("SELECT COUNT(*) FROM employee_master WHERE em_employee_active = 1;")
            total_employees = c.fetchone()[0]

            c.execute(""" 
            SELECT 
                (SELECT COUNT(DISTINCT et_employee_id) 
                FROM employee_transactions 
                WHERE DATE(et_employee_in_time) = CURRENT_DATE) / 
                (SELECT COUNT(*) 
                FROM employee_master 
                WHERE em_employee_active = 1) * 100 AS attendance_rate;
            """)
            attendance_rate = c.fetchone()[0] or 0 

            c.execute(""" 
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
            attendance_by_department = c.fetchall()

            attendance_data = [
                (dept, attendance_count, (attendance_count / employee_count) * 100 if employee_count > 0 else 0)
                for dept, employee_count, attendance_count in attendance_by_department
            ] 
            return total_employees, attendance_rate, attendance_data
        
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return 0, 0, []

    def update_plot(departments, attendance_percentages):
        ax.clear() 
        bars = ax.barh(departments, attendance_percentages, color='blue') 
        ax.set_xlabel('Attendance %')  
        ax.set_ylabel('Departments')  
        ax.set_title('Attendance by Department')
        ax.set_xlim(0, 100)

        for bar, percentage in zip(bars, attendance_percentages):
            xval = bar.get_width()
            ax.text(xval + 1, bar.get_y() + bar.get_height() / 2, f"{percentage:.2f}%", va='center')
            
        # plt.subplots_adjust(left=0.2) 
        fig.tight_layout()  

        canvas.draw()

    def update_frame():
        total_employees, attendance_rate, attendance_by_department = fetch_daily_data()

        total_employees_label.config(text=f"Total Employees: {total_employees}")
        attendance_rate_label.config(text=f"Attendance Rate: {attendance_rate:.2f}%")

        progress_bar['value'] = attendance_rate

        for row in department_tree.get_children():
            department_tree.delete(row)

        departments = []
        attendance_percentages = []
        
        for dept_desc, attendance_count, attendance_percentage in attendance_by_department:
            department_tree.insert("", "end", values=(dept_desc, attendance_count))
            departments.append(dept_desc)
            attendance_percentages.append(attendance_percentage)

        update_plot(departments, attendance_percentages)

    
    label_frame = tk.Frame(admin_dashboard_frame)
    label_frame.pack(pady=10)

    total_employees_label = tk.Label(label_frame, text="Total Employees: ", font=("Arial", 16))
    total_employees_label.pack(side="left", padx=10)
    attendance_rate_label = tk.Label(label_frame, text="Attendance Rate: ", font=("Arial", 16))
    attendance_rate_label.pack(side="left", padx=10)

    progress_bar = ttk.Progressbar(label_frame, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(side="right", pady=10)

    department_frame = tk.Frame(admin_dashboard_frame)
    department_frame.pack(pady=10)

    left_frame = tk.Frame(department_frame)
    left_frame.pack(side="left", padx=10, pady=10)

    date_label = tk.Label(left_frame, text=f"Date: {datetime.now().strftime('%d-%m-%Y')}, Day: {datetime.now().strftime('%A')}", font=("Arial", 15))
    date_label.pack(anchor="nw")  
    department_tree = ttk.Treeview(left_frame, columns=("Department Description", "Attendance"), show="headings", height=5)
    department_tree.heading("Department Description", text="Department Description")
    department_tree.heading("Attendance", text="Attendance")
    department_tree.pack(pady=20)  

    graph_frame = tk.Frame(department_frame)
    graph_frame.pack(side="left", padx=10, pady=10)

    fig = plt.Figure(figsize=(5, 3), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()

    left_frame = tk.Frame(admin_dashboard_frame)
    left_frame.pack(side='left', padx=10, pady=10, fill='both', expand=True)

    button_frame1 = tk.Frame(left_frame)
    button_frame1.pack(side="top", fill="x")
    tk.Button(button_frame1, text="View Employees", command=lambda: [setup_view_employees_frame(), show_frame(view_employees_frame)]).pack(side="left", padx=5, pady=5, expand=True, fill='x')
    tk.Button(button_frame1, text="View Attendance", command=lambda: [setup_view_attendance_frame(), show_frame(view_attendance_frame)]).pack(side="left", padx=5, pady=5, expand=True, fill='x')

    tk.Button(left_frame, text="Open Registration", command=lambda: [setup_open_registration_frame(), show_frame(open_registration_frame)]).pack(fill="x", padx=5, pady=5)

    button_frame2 = tk.Frame(left_frame)
    button_frame2.pack(side="top", fill="x")
    tk.Button(button_frame2, text="Add New Admin", command=lambda: [setup_add_admin_frame(), show_frame(add_admin_frame)]).pack(side="left", padx=5, pady=5, expand=True, fill='x')
    tk.Button(button_frame2, text="Change Admin Password", command=lambda: [setup_change_admin_password_frame(), show_frame(change_admin_password_frame)]).pack(side="left", padx=5, pady=5, expand=True, fill='x')

    right_frame = tk.Frame(admin_dashboard_frame)
    right_frame.pack(side='right', padx=10, pady=10, fill='both', expand=True)

    refresh_button = tk.Button(right_frame, text="Refresh", command=update_frame)
    refresh_button.pack(side="top", pady=5, padx=10, fill='x')

    back_button = tk.Button(right_frame, text="Back to Main Screen", command=lambda: show_frame(main_frame))
    back_button.pack(side="top", pady=5, padx=10, fill='x')
    
    update_frame()
    
    
    def setup_view_employees_frame():
        for widget in view_employees_frame.winfo_children():
            widget.destroy()

        tk.Label(view_employees_frame, text="Registered Employees", font=("Arial", 16)).pack(pady=10)
        
        c.execute("""SELECT em.em_employee_id, em.em_employee_name, em.em_employee_dept, dm.dm_dept_desc, em.em_employee_desg
                FROM 
                    employee_master em
                JOIN 
                    department_master dm 
                ON 
                    em.em_employee_dept = dm.dm_dept_id
                WHERE 
                    em.em_employee_active = 1 AND dm.dm_dept_active = 1;        
        """)
        records = c.fetchall()
        
        tree = ttk.Treeview(view_employees_frame, columns=('Employee ID', 'Name', 'Department','Department Name', 'Designation'), show='headings')
        tree.heading('Employee ID', text="Employee ID")
        tree.heading('Name', text="Name")
        tree.heading('Department', text="Department")
        tree.heading('Department Name', text="Department Name")
        tree.heading('Designation', text="Designation")
        
        for row in records:
            tree.insert('', 'end', values=row)
        
        tree.pack(fill="both", expand=True)

        back_button = tk.Button(view_employees_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame))
        back_button.pack(pady=10)

    class InvalidDepartmentSelectionError(Exception):
        pass

    def setup_view_attendance_frame():
        for widget in view_attendance_frame.winfo_children():
            widget.destroy()

        tk.Label(view_attendance_frame, text="Attendance Records", font=("Arial", 16)).pack(pady=10)

        c.execute("SELECT dm_dept_desc FROM department_master")
        departments = [row[0] for row in c.fetchall()]

        tk.Label(view_attendance_frame, text="Select Department").pack(pady=5)
        view_department = ttk.Combobox(view_attendance_frame, values=departments)
        view_department.pack(pady=5)
        view_department.set('Select Department')

        tk.Label(view_attendance_frame, text="Start Date (YYYY-MM-DD)").pack(pady=5)
        entry_start_date = DateEntry(view_attendance_frame, date_pattern='yyyy-mm-dd')
        entry_start_date.pack(pady=5)

        tk.Label(view_attendance_frame, text="End Date (YYYY-MM-DD)").pack(pady=5)
        entry_end_date = DateEntry(view_attendance_frame, date_pattern='yyyy-mm-dd')
        entry_end_date.pack(pady=5)

        def display_attendance(selected_department):
            for widget in view_attendance_frame.winfo_children():
                if isinstance(widget, tk.Frame) or isinstance(widget, ttk.Treeview):
                    widget.destroy()

            if hasattr(view_attendance_frame, 'back_button'):
                view_attendance_frame.back_button.destroy()
            
            try:

                if selected_department == 'Select Department':
                    raise InvalidDepartmentSelectionError("Please select a valid department.")
                    
                start_date = entry_start_date.get()
                end_date = entry_end_date.get()
                
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  

                c.execute('''
                    SELECT em.em_employee_id, em.em_employee_name 
                    FROM employee_master em
                    JOIN department_master d ON em.em_employee_dept = d.dm_dept_id
                    WHERE d.dm_dept_desc = %s
                ''', (selected_department,))
                employees = c.fetchall()

                department_frame = tk.Frame(view_attendance_frame, borderwidth=2, relief="groove")
                department_frame.pack(fill="both", expand=True, padx=10, pady=10)

                label = tk.Label(department_frame, text=selected_department, font=("Arial", 14, "bold"))
                label.pack(pady=5)

                tree = ttk.Treeview(department_frame, columns=('Date', 'Status', 'Employee ID', 'Name', 'Checkin_time', 'Checkout_time', 'Worked For'), show='headings')
                tree.heading('Date', text="Date")
                tree.heading('Status', text="Status")
                tree.heading('Employee ID', text="Employee ID")
                tree.heading('Name', text="Name")
                tree.heading('Checkin_time', text="Checkin Time")
                tree.heading('Checkout_time', text="Checkout Time")
                tree.heading('Worked For', text="Worked For")

                c.execute('''
                    SELECT DATE(et.et_employee_in_time), et.et_employee_id, em.em_employee_name, et.et_employee_in_time, et.et_employee_out_time, et.et_worktime
                    FROM employee_transactions et
                    JOIN employee_master em ON et.et_employee_id = em.em_employee_id
                    JOIN department_master d ON em.em_employee_dept = d.dm_dept_id
                    WHERE d.dm_dept_desc = %s AND et.et_employee_in_time >= %s AND et.et_employee_in_time < %s;
                ''', (selected_department, start_datetime, end_datetime))

                export_records = c.fetchall()
                full_date_range = [start_datetime + timedelta(days=i) for i in range((end_datetime - start_datetime).days)]

                for single_date in full_date_range:
                    date_str = single_date.strftime('%Y-%m-%d')

                    c.execute('''
                        SELECT et.et_employee_id, em.em_employee_name, et.et_employee_in_time, et.et_employee_out_time, et.et_worktime
                        FROM employee_transactions et
                        JOIN employee_master em ON et.et_employee_id = em.em_employee_id
                        WHERE et.et_employee_in_time >= %s AND et.et_employee_in_time < %s AND em.em_employee_dept = (
                            SELECT dm_dept_id FROM department_master WHERE dm_dept_desc = %s
                        )
                    ''', (single_date, single_date + timedelta(days=1), selected_department))
                    present_records = c.fetchall()

                    present_employee_ids = {record[0] for record in present_records}

                    for record in present_records:
                        employee_id, employee_name, checkin_time, checkout_time, worked_for = record
                        tree.insert('', 'end', values=(date_str, "Present", employee_id, employee_name, checkin_time, checkout_time, worked_for))

                    for employee_id, employee_name in employees:
                        if employee_id not in present_employee_ids:
                            tree.insert('', 'end', values=(date_str, "Absent", employee_id, employee_name, "-", "-", "-"))


                tree.pack(fill="both", expand=True)

                button_frame = tk.Frame(view_attendance_frame)
                button_frame.pack(pady=10)
                view_attendance_frame.button_frame = button_frame

                export_button = tk.Button(button_frame, text="Export to Excel", command=lambda: export_to_excel(export_records))
                export_button.pack(side="left", padx=5)

                back_button = tk.Button(button_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame))
                back_button.pack(side="left", padx=5)
 
            except InvalidDepartmentSelectionError as e:
                messagebox.showerror("Error", str(e))
                view_attendance_frame.back_button = tk.Button(view_attendance_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame))
                view_attendance_frame.back_button.pack(pady=10)


        def export_to_excel(records):
            if not records:
                messagebox.showerror("Error", "No data available to export.")
                return

            df = pd.DataFrame(records, columns=['Date', 'Employee ID', 'Name', 'Checkin Time', 'Checkout Time', 'Worked For'])

            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                try:
                    df.to_excel(file_path, index=False)
                    messagebox.showinfo("Success", f"Attendance data has been exported to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export data: {str(e)}")

        view_button = tk.Button(view_attendance_frame, text="View Attendance", command=lambda: display_attendance(view_department.get()))
        view_button.pack(pady=10)

        view_attendance_frame.back_button = tk.Button(view_attendance_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame))
        view_attendance_frame.back_button.pack(pady=10)
        

    def setup_open_registration_frame():
        for widget in open_registration_frame.winfo_children():
            widget.destroy()

        tk.Label(open_registration_frame, text="Employee Registration", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(open_registration_frame, text="Employee ID").pack()
        entry_emp_id = tk.Entry(open_registration_frame)
        entry_emp_id.pack()
        
        tk.Label(open_registration_frame, text="Employee Name").pack()
        entry_name = tk.Entry(open_registration_frame)
        entry_name.pack()
        
        
        c.execute("SELECT dm_dept_desc FROM department_master")
        departments = [row[0] for row in c.fetchall()]
        tk.Label(open_registration_frame, text="Department").pack()
        entry_department = ttk.Combobox(open_registration_frame, values=departments)
        entry_department.pack()
        entry_department.set('Select Department')

        c.execute("SELECT dsgm_desc FROM designation_master")
        designations = [row[0] for row in c.fetchall()]
        tk.Label(open_registration_frame, text="Designation").pack()
        entry_designation = ttk.Combobox(open_registration_frame, values=designations)
        entry_designation.pack()
        entry_designation.set('Select Designation')
        
        def capture_image():
            capture_window = tk.Toplevel(open_registration_frame)
            capture_window.title("Capture Image")
            
            lmain = tk.Label(capture_window)
            lmain.pack()
            
            cap = cv2.VideoCapture(0)
            
            def update_frame():
                ret, frame = cap.read()
                if ret:
                    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    img = Image.fromarray(cv2image)
                    imgtk = ImageTk.PhotoImage(image=img)
                    lmain.imgtk = imgtk
                    lmain.configure(image=imgtk)
                    lmain.after(10, update_frame)
                else:
                    cap.release()
                    capture_window.destroy()
                    messagebox.showerror("Error", "Failed to access camera.")
                    return

            def capture_and_save():
                ret, frame = cap.read()
                if ret:
                    cap.release()
                    capture_window.destroy()
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    if len(face_locations) == 0:
                        messagebox.showerror("Error", "No face detected in the image.")
                        return
                    elif len(face_locations) > 1:
                        messagebox.showerror("Error", "Multiple faces detected. Ensure only one face is in the frame.")
                        return
                    face_encoding = face_recognition.face_encodings(rgb_small_frame, face_locations)[0]
                    
                    encoding_data = face_encoding.tobytes()
                    
                    emp_id = entry_emp_id.get()
                    emp_name = entry_name.get()
                    emp_department = entry_department.get()
                    emp_designation = entry_designation.get()

                    output_dir = "C:\\Users\\kumar\\Desktop\\register"

                    if len(face_locations) > 0:
                        y1, x2, y2, x1 = face_locations[0]
                    face_image = frame[y1*4:y2*4, x1*4:x2*4]

                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
            
                    image_path = os.path.join(output_dir, f"{emp_id}.jpg")
                    
                    cv2.imwrite(image_path, face_image)

                    if emp_id == '' or emp_name == '' or emp_department == '' or emp_designation == '':
                        messagebox.showerror("Error", "Please fill all the fields.")
                        return
                    
                    c.execute("SELECT dm_dept_id FROM department_master WHERE dm_dept_desc=%s", (emp_department,))
                    emp_dept_id = c.fetchone()[0]
                    if emp_dept_id is None:
                        messagebox.showerror("Error", "Department not found.")
                        return
                    
                    c.execute("SELECT dsgm_id FROM designation_master WHERE dsgm_desc=%s", (emp_designation,))
                    emp_desg_id = c.fetchone()[0]
                    if emp_desg_id is None:
                        messagebox.showerror("Error", "Designation not found.")
                        return
                    
                    c.execute("SELECT * FROM employee_master WHERE em_employee_id=%s", (emp_id,))
                    if c.fetchone() is not None:
                        messagebox.showerror("Error", "Employee ID already exists.")
                        return
                    
                    c.execute("INSERT INTO employee_master (em_employee_id, em_employee_name, em_employee_dept, em_employee_desg, em_employee_face_encoding, em_employee_imgpth) VALUES (%s, %s, %s, %s, %s, %s)",
                            (emp_id, emp_name, emp_dept_id, emp_desg_id, encoding_data, image_path))
                    conn.commit()
                    messagebox.showinfo("Success", "Employee registered successfully.")
                    show_frame(admin_dashboard_frame)
                else:
                    cap.release()
                    capture_window.destroy()
                    messagebox.showerror("Error", "Failed to capture image.")
            
            btn_capture = tk.Button(capture_window, text="Capture", command=capture_and_save)
            btn_capture.pack()
            
            def on_closing():
                cap.release()
                capture_window.destroy()
            
            capture_window.protocol("WM_DELETE_WINDOW", on_closing)
            update_frame()

        btn_capture = tk.Button(open_registration_frame, text="Capture Image", command=capture_image)
        btn_capture.pack(pady=20)

        back_button = tk.Button(open_registration_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame))
        back_button.pack(pady=10)

    def setup_add_admin_frame():
        for widget in add_admin_frame.winfo_children():
            widget.destroy()

        tk.Label(add_admin_frame, text="Add New Admin", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(add_admin_frame, text="Username").pack()
        entry_new_admin_username = tk.Entry(add_admin_frame)
        entry_new_admin_username.pack()
        
        tk.Label(add_admin_frame, text="Password").pack()
        entry_new_admin_password = tk.Entry(add_admin_frame, show="*")
        entry_new_admin_password.pack()
        
        def save_new_admin():
            new_username = entry_new_admin_username.get()
            new_password = entry_new_admin_password.get()
            
            if new_username == '' or new_password == '':
                messagebox.showerror("Error", "Please fill all fields.")
                return
            
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            try:
                c.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (new_username, hashed_password))
                conn.commit()
                messagebox.showinfo("Success", "New admin added successfully.")
                show_frame(admin_dashboard_frame)
            except mysql.connector.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")
        
        btn_save = tk.Button(add_admin_frame, text="Save", command=save_new_admin)
        btn_save.pack(pady=10)

        tk.Button(add_admin_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame)).pack(pady=10)


    def setup_change_admin_password_frame():
        for widget in change_admin_password_frame.winfo_children():
            widget.destroy()

        tk.Label(change_admin_password_frame, text="Change Admin Password", font=("Arial", 16)).pack(pady=10)

        tk.Label(change_admin_password_frame, text="Old Password").pack(pady=5)
        entry_old_password = tk.Entry(change_admin_password_frame, show="*")
        entry_old_password.pack(pady=5)

        tk.Label(change_admin_password_frame, text="New Password").pack(pady=5)
        entry_new_password = tk.Entry(change_admin_password_frame, show="*")
        entry_new_password.pack(pady=5)

        tk.Label(change_admin_password_frame, text="Confirm Password").pack(pady=5)
        entry_confirm_password = tk.Entry(change_admin_password_frame, show="*")
        entry_confirm_password.pack(pady=5)

        def update_password():
            old_password = entry_old_password.get()
            new_password = entry_new_password.get()
            confirm_password = entry_confirm_password.get()

            if new_password != confirm_password:
                messagebox.showerror("Error", "New passwords do not match.")
                return

            c.execute("SELECT password FROM admins WHERE username = 'admin'")
            result = c.fetchone()
            if result:
                hashed_password = result[0]

                if bcrypt.checkpw(old_password.encode('utf-8'), hashed_password.encode('utf-8')):
                    new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    c.execute("UPDATE admins SET password = %s WHERE username = 'admin'", (new_hashed_password.decode('utf-8'),))
                    conn.commit()
                    messagebox.showinfo("Success", "Password updated.")
                    show_frame(admin_dashboard_frame)
                else:
                    messagebox.showerror("Error", "Old password is incorrect.")
            else:
                messagebox.showerror("Error", "Admin user not found.")

        btn_change = tk.Button(change_admin_password_frame, text="Change Password", command=update_password)
        btn_change.pack(pady=10)

        btn_back_home = tk.Button(change_admin_password_frame, text="Back to Dashboard", command=lambda: show_frame(admin_dashboard_frame))
        btn_back_home.pack(pady=10)



def setup_attendance_frame():
    for widget in open_registration_frame.winfo_children():
            widget.destroy()

    tk.Label(attendance_frame, text="Employee ID:").pack(pady=10)
    employee_id_entry = tk.Entry(attendance_frame)
    employee_id_entry.pack(pady=5)

    def save_face_image(frame, face_loc, id, output_dir):
        y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
        face_image = frame[y1*4:y2*4, x1*4:x2*4] 

        cv2.imshow("Captured image", frame)
        cv2.waitKey(2000) 
        cv2.destroyAllWindows()

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        image_path = os.path.join(output_dir, f"{id}.jpg")
        cv2.imwrite(image_path, face_image)
        return image_path
    
    
    def mark_attendance(is_markin=True):

        cap = cv2.VideoCapture(0)

        emp_id = employee_id_entry.get().strip()
        if not emp_id:
            messagebox.showerror("Error", "Employee ID is required.")
            cap.release()
            return

        output_dir = "C:\\Users\\kumar\\Desktop\\attend"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().date()
        date_today = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join(output_dir, date_today)
        
        try:
            c.execute("""   SELECT * FROM employee_transactions
                    WHERE et_employee_id=%s AND DATE(et_employee_in_time)=%s AND DATE(et_employee_out_time)=%s
                    """, (emp_id, date_today, date_today))
            existing_record = c.fetchone()

            if existing_record:
                messagebox.showinfo("Attendance", "Attendance already marked for today.")
                return
        
            ret, frame = cap.read()
            if ret:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_small_frame)
                if len(face_locations) == 0:
                    messagebox.showerror("Error", "No face detected.")
                    return

                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                c.execute("SELECT em_employee_name, em_employee_face_encoding FROM employee_master WHERE em_employee_id=%s", (emp_id,))
                record = c.fetchone()

                if not record:
                    messagebox.showerror("Error", "Employee not found.")
                    return

                name = record[0]
                known_face_encoding = np.frombuffer(record[1])

                FACE_DISTANCE_THRESHOLD = 0.6

                if len(face_encodings) > 0:
                    face_encoding = face_encodings[0]  
                    match = face_recognition.compare_faces([known_face_encoding], face_encoding)
                    face_distance = face_recognition.face_distance([known_face_encoding], face_encoding)[0]

                    percentage_match = max(0, (1 - face_distance / FACE_DISTANCE_THRESHOLD) * 100)

                    if match[0] and face_distance < FACE_DISTANCE_THRESHOLD:
                        if is_markin:
                            c.execute("SELECT * FROM employee_transactions WHERE et_employee_id=%s AND DATE(et_employee_in_time)=%s AND et_employee_out_time IS NULL", (emp_id, date_today))
                            record = c.fetchone()
                            if record:
                                messagebox.showinfo("Attendance", f"{name} has already checked in today.")
                                return

                            transaction_id = [None]
                            c.callproc('generate_transaction_id', transaction_id)
                            for result in c.stored_results():
                                transaction_id = result.fetchone()[0]
                                
                            output_dir_in = os.path.join(output_dir, "employee_in_imgpth")
                            image_path = save_face_image(frame, face_locations[0], transaction_id, output_dir_in)

                            c.execute("INSERT INTO employee_transactions (et_transaction_id, et_employee_id, et_employee_in_time, et_employee_in_imgpth, et_percentage_match) VALUES (%s, %s, %s, %s, %s)",
                                        (transaction_id, emp_id, timestamp, image_path, percentage_match))
                            conn.commit()
                            messagebox.showinfo("Attendance", f"Checked in {name} at {timestamp}")

                        else:  # Mark out

                            c.execute("SELECT * FROM employee_transactions WHERE et_employee_id=%s AND DATE(et_employee_in_time)=%s AND et_employee_out_time IS NULL", (emp_id, date_today))
                            record = c.fetchone()
                            if not record:
                                messagebox.showerror("Error", f"{name} has not checked in today.")
                                return

                            transaction_id = record[0]
                            output_dir_out = os.path.join(output_dir, "employee_out_imgpth")
                            image_path = save_face_image(frame, face_locations[0], transaction_id, output_dir_out)
                                
                            c.execute("UPDATE employee_transactions SET et_employee_out_time=%s, et_employee_out_imgpth=%s, et_worktime = TIMEDIFF(et_employee_out_time, et_employee_in_time) WHERE et_employee_id=%s AND DATE(et_employee_in_time)=%s AND et_employee_out_time IS NULL",
                                        (timestamp, image_path, emp_id, date_today))
                            conn.commit()
                            messagebox.showinfo("Attendance", f"Checked out {name} at {timestamp}")

                        return
                    
                    else:
                        output_dir = "C:\\Users\\kumar\\Desktop\\failed_attempts"
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        output_dir = os.path.join(output_dir, emp_id)

                        error_image_path = save_face_image(frame, face_locations[0], timestamp, output_dir)

                        c.execute("""SELECT eae_failed_attempts FROM employee_attendance_errors WHERE eae_employee_id=%s AND eae_date=%s """,
                                    (emp_id, date))
                        error_record = c.fetchone()
                        
                        if error_record:
                            c.execute("""UPDATE employee_attendance_errors SET eae_failed_attempts = eae_failed_attempts + 1, eae_failedattempt_image_path=%s
                                            WHERE eae_employee_id=%s AND eae_date=%s """,
                                        (error_image_path, emp_id, date))
                        else:
                            c.execute("""INSERT INTO employee_attendance_errors (eae_employee_id, eae_date, eae_failed_attempts, eae_failedattempt_image_path)
                                        VALUES (%s, %s, 1, %s)""",
                                        (emp_id, date, error_image_path))

                        messagebox.showerror("Error", "Face not recognized.")
                        return
                else:
                    messagebox.showerror("Error", "No face encodings found.")
                    return
            else:
                messagebox.showerror("Error", "Failed to capture image.")
                return
        finally:
            cap.release()
            employee_id_entry.delete(0, tk.END)
    
    btn_mark_in = tk.Button(attendance_frame, text="Mark In", command=lambda: mark_attendance(is_markin=True))
    btn_mark_in.pack(pady=10)

    btn_mark_out = tk.Button(attendance_frame, text="Mark Out", command=lambda: mark_attendance(is_markin=False))
    btn_mark_out.pack(pady=10)

    btn_back = tk.Button(attendance_frame, text="Back to Main Screen", command=lambda: [employee_id_entry.delete(0, tk.END), show_frame(main_frame)])
    btn_back.pack(pady=10)


setup_main_frame()
setup_admin_login_frame()
setup_attendance_frame()

show_frame(main_frame)

root.mainloop()