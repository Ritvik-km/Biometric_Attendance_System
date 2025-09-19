"""
Face Recognition Service Module
Handles all face detection, encoding, and recognition operations
"""
import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime

class FaceRecognitionService:
    def __init__(self):
        self.FACE_DISTANCE_THRESHOLD = 0.6

    def capture_image_from_camera(self):
        """Capture image from camera"""
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        return ret, frame

    def detect_faces(self, frame):
        """Detect faces in the frame and return face locations"""
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        return face_locations, rgb_small_frame

    def encode_face(self, rgb_frame, face_locations):
        """Generate face encoding from detected face"""
        if len(face_locations) == 0:
            return None, "No face detected in the image."
        elif len(face_locations) > 1:
            return None, "Multiple faces detected. Ensure only one face is in the frame."
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if len(face_encodings) > 0:
            return face_encodings[0], None
        return None, "Could not encode face."

    def compare_faces(self, known_face_encoding, face_encoding):
        """Compare face encodings and determine if they match"""
        if known_face_encoding is None or face_encoding is None:
            return False, 1.0
        
        face_distance = face_recognition.face_distance([known_face_encoding], face_encoding)[0]
        matches = face_distance <= self.FACE_DISTANCE_THRESHOLD
        return matches, face_distance

    def extract_and_save_face(self, frame, face_locations, emp_id, output_dir):
        """Extract face from frame and save to directory"""
        if len(face_locations) > 0:
            y1, x2, y2, x1 = face_locations[0]
            face_image = frame[y1*4:y2*4, x1*4:x2*4]

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            image_path = os.path.join(output_dir, f"{emp_id}.jpg")
            cv2.imwrite(image_path, face_image)
            return image_path
        return None

    def save_face_image(self, frame, face_loc, id, output_dir):
        """Save face image for attendance tracking"""
        y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
        face_image = frame[y1*4:y2*4, x1*4:x2*4]

        # Display captured image briefly
        cv2.imshow("Captured image", frame)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        image_path = os.path.join(output_dir, f"{id}.jpg")
        cv2.imwrite(image_path, face_image)
        return image_path

    def process_attendance_image(self, emp_id):
        """Process image for attendance marking"""
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None, None, "Failed to capture image."
        
        face_locations, rgb_small_frame = self.detect_faces(frame)
        
        if len(face_locations) == 0:
            return None, None, "No face detected."
        
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]
            return frame, face_encoding, None
        
        return None, None, "Could not encode face."

    def validate_employee_face(self, face_encoding, known_face_encoding_bytes):
        """Validate employee face against stored encoding"""
        if known_face_encoding_bytes is None:
            return False, 1.0
        
        known_face_encoding = np.frombuffer(known_face_encoding_bytes)
        return self.compare_faces(known_face_encoding, face_encoding)

    def create_camera_window_update_function(self, lmain, cap, capture_window):
        """Create update function for camera preview window"""
        def update_frame():
            ret, frame = cap.read()
            if ret:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                from PIL import Image, ImageTk
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                lmain.imgtk = imgtk
                lmain.configure(image=imgtk)
                lmain.after(10, update_frame)
            else:
                cap.release()
                capture_window.destroy()
                from tkinter import messagebox
                messagebox.showerror("Error", "Failed to access camera.")
        return update_frame