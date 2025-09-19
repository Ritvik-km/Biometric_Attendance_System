# Biometric Attendance System - Microservices Architecture

This repository contains a biometric attendance system that has been refactored from a monolithic architecture to a microservices-based approach.

## Architecture Overview

The system has been transformed from a single monolithic file (`app_display.py` - 865 lines) into a modular microservices architecture with 5 focused services:

### Microservices

1. **`main_app.py`** (408 lines) - Main Application Entry Point
   - Orchestrates all services
   - Provides the complete GUI interface using Tkinter
   - Handles service dependency injection
   - Maintains the original user experience

2. **`database_service.py`** (185 lines) - Database Operations Service
   - Database connection and initialization
   - Admin management (authentication, CRUD operations)  
   - Employee management (registration, retrieval)
   - Attendance operations (check-in/out, records)
   - Department management

3. **`face_recognition_service.py`** (128 lines) - Face Recognition Service
   - Camera operations and image capture
   - Face detection and location identification
   - Face encoding generation and comparison
   - Image processing and storage
   - Camera preview window management

4. **`admin_service.py`** (107 lines) - Admin Management Service
   - Admin authentication and password management
   - Dashboard data aggregation
   - Employee registration workflow
   - Department validation

5. **`attendance_service.py`** (143 lines) - Attendance Operations Service
   - Attendance marking (check-in/check-out)
   - Face validation for attendance
   - Attendance records retrieval and filtering
   - Excel export functionality
   - Failed attempt logging

## Usage

### Running the Application

To run the new microservices-based application:

```bash
python3 main_app.py
```

### Legacy Version

The original monolithic version is still available in `app_display.py` for reference, but the new microservices architecture is recommended for all use cases.

## Benefits of Microservices Architecture

- **Separation of Concerns**: Each service has a single, well-defined responsibility
- **Maintainability**: Easier to modify and extend individual components
- **Testability**: Services can be tested independently
- **Modularity**: Clear interfaces between services
- **Scalability**: Individual services can be optimized or replaced as needed

## Dependencies

The application requires the following Python packages:
- `tkinter` (GUI framework)
- `opencv-python` (cv2 - computer vision operations)
- `face_recognition` (face detection and recognition)
- `mysql-connector-python` (database connectivity)
- `numpy` (numerical operations)
- `PIL/Pillow` (image processing)
- `tkcalendar` (date picker widget)
- `bcrypt` (password hashing)
- `pandas` (data manipulation)
- `matplotlib` (plotting and visualization)
- `python-dotenv` (environment variable management)

## Environment Setup

1. Install required dependencies:
```bash
pip install opencv-python face_recognition mysql-connector-python numpy Pillow tkcalendar bcrypt pandas matplotlib python-dotenv
```

2. Set up your database configuration in a `.env` file:
```
host=your_database_host
user=your_database_user
password=your_database_password
database=your_database_name
```

3. Run the application:
```bash
python3 main_app.py
```

## File Structure

```
.
├── main_app.py                    # Main application entry point
├── database_service.py            # Database operations service
├── face_recognition_service.py    # Face recognition service
├── admin_service.py               # Admin management service
├── attendance_service.py          # Attendance operations service
├── app_display.py                 # Legacy monolithic version
├── .env                          # Environment configuration
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Refactoring Summary

- **Original**: 1 file, 865 lines, monolithic architecture
- **Refactored**: 5 services, 971 lines total, microservices architecture  
- **Increase**: +106 lines (12% increase for much better architecture)

The slight increase in total lines is due to proper class structures, comprehensive documentation, better error handling, and clear separation of concerns. This is a worthwhile trade-off for the significant improvements in maintainability and modularity.