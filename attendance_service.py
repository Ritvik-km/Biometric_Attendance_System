"""
Attendance Service Module
Handles attendance marking and viewing operations
"""
import os
import pandas as pd
import face_recognition
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog

class AttendanceService:
    def __init__(self, database_service, face_recognition_service):
        self.db = database_service
        self.face_service = face_recognition_service

    def mark_attendance(self, emp_id, is_markin=True):
        """Mark attendance for an employee"""
        if not emp_id:
            return False, "Employee ID is required."

        # Process image for attendance
        frame, face_encoding, error = self.face_service.process_attendance_image(emp_id)
        if error:
            return False, error

        # Get employee record
        employee_record = self.db.get_employee_by_id(emp_id)
        if not employee_record:
            return False, "Employee not found."

        name = employee_record[0]
        known_face_encoding = employee_record[1]

        # Validate face
        is_match, face_distance = self.face_service.validate_employee_face(face_encoding, known_face_encoding)
        
        if is_match:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_today = datetime.now().strftime("%Y-%m-%d")
            
            if is_markin:
                return self._handle_checkin(emp_id, name, timestamp, frame, face_encoding)
            else:
                return self._handle_checkout(emp_id, name, timestamp, date_today, frame, face_encoding)
        else:
            # Save failed attempt image
            self._save_failed_attempt(emp_id, frame, face_encoding)
            return False, f"Face recognition failed. Distance: {face_distance:.3f}"

    def _handle_checkin(self, emp_id, name, timestamp, frame, face_encoding):
        """Handle employee check-in"""
        date_today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if already checked in today
        existing_record = self.db.check_attendance_exists(emp_id, date_today)
        if existing_record:
            return False, "Attendance already marked for today."
        
        # Save image and add attendance record
        output_dir = "C:\\Users\\kumar\\Desktop\\attend"
        output_dir = os.path.join(output_dir, date_today)
        
        image_path = self.face_service.save_face_image(frame, face_recognition.face_locations(frame), emp_id, output_dir)
        transaction_id = self.db.add_attendance_in(emp_id, timestamp, image_path)
        
        return True, f"Checked in {name} at {timestamp}"

    def _handle_checkout(self, emp_id, name, timestamp, date_today, frame, face_encoding):
        """Handle employee check-out"""
        # Check if there's a check-in record for today
        existing_record = self.db.check_attendance_exists(emp_id, date_today)
        if not existing_record:
            return False, "No check-in record found for today."
        
        # Save checkout image
        output_dir_out = "C:\\Users\\kumar\\Desktop\\attend"
        output_dir_out = os.path.join(output_dir_out, date_today)
        
        image_path = self.face_service.save_face_image(frame, face_recognition.face_locations(frame), f"{emp_id}_out", output_dir_out)
        self.db.update_attendance_out(emp_id, timestamp, image_path, date_today)
        
        return True, f"Checked out {name} at {timestamp}"

    def _save_failed_attempt(self, emp_id, frame, face_encoding):
        """Save failed attendance attempt image"""
        output_dir = "C:\\Users\\kumar\\Desktop\\failed_attempts"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = os.path.join(output_dir, emp_id)
        
        self.face_service.save_face_image(frame, face_recognition.face_locations(frame), timestamp, output_dir)

    def get_attendance_records(self, selected_department, start_date, end_date):
        """Get attendance records for a department within date range"""
        try:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)
            
            export_records = self.db.get_attendance_records(selected_department, start_datetime, end_datetime)
            
            # Generate full date range for display
            attendance_display_data = []
            full_date_range = [start_datetime + timedelta(days=i) for i in range((end_datetime - start_datetime).days)]

            for single_date in full_date_range:
                date_str = single_date.strftime('%Y-%m-%d')
                daily_records = self.db.get_daily_attendance_records(selected_department, single_date.date())
                
                if daily_records:
                    for record in daily_records:
                        emp_id, emp_name, checkin_time, checkout_time, worktime = record
                        
                        checkin_display = checkin_time.strftime('%H:%M:%S') if checkin_time else "N/A"
                        checkout_display = checkout_time.strftime('%H:%M:%S') if checkout_time else "N/A"
                        worktime_display = str(worktime) if worktime else "N/A"
                        
                        attendance_display_data.append((date_str, emp_id, emp_name, checkin_display, checkout_display, worktime_display))
                else:
                    attendance_display_data.append((date_str, "No records", "", "", "", ""))
            
            return attendance_display_data, export_records
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch attendance data: {str(e)}")
            return [], []

    def export_attendance_to_excel(self, records):
        """Export attendance records to Excel file"""
        if not records:
            messagebox.showerror("Error", "No data available to export.")
            return False
        
        df = pd.DataFrame(records, columns=['Date', 'Employee ID', 'Name', 'Checkin Time', 'Checkout Time', 'Worked For'])
        
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Attendance data has been exported to {file_path}")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")
                return False
        return False