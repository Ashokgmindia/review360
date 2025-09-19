"""
Utility functions for handling bulk uploads of users (teachers and students).
Supports Excel (.xlsx), CSV (.csv), and JSON (.json) file formats.
These functions only create User accounts, not Teacher/Student model records.
"""

import pandas as pd
import json
import io
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from iam.models import College
from .models import Teacher, Student, Department, Class

User = get_user_model()


class BulkUploadError(Exception):
    """Custom exception for bulk upload errors."""
    pass


class BulkUploadProcessor:
    """Base class for processing bulk uploads."""
    
    def __init__(self, file, college, uploaded_by):
        self.file = file
        self.college = college
        self.uploaded_by = uploaded_by
        self.errors = []
        self.success_count = 0
        self.data = None
        
    def validate_file_format(self):
        """Validate that the file is in a supported format."""
        file_extension = self.file.name.split('.')[-1].lower()
        if file_extension not in ['xlsx', 'csv', 'json']:
            raise BulkUploadError(f"Unsupported file format: {file_extension}. Supported formats: xlsx, csv, json")
        return file_extension
    
    def parse_file(self):
        """Parse the uploaded file and return a DataFrame."""
        file_extension = self.validate_file_format()
        
        try:
            if file_extension == 'xlsx':
                self.data = pd.read_excel(self.file)
            elif file_extension == 'csv':
                self.data = pd.read_csv(self.file)
            elif file_extension == 'json':
                with self.file.open('r') as f:
                    json_data = json.load(f)
                self.data = pd.DataFrame(json_data)
        except Exception as e:
            raise BulkUploadError(f"Error parsing file: {str(e)}")
        
        if self.data.empty:
            raise BulkUploadError("File is empty or contains no data")
        
        return self.data


class TeacherBulkUploadProcessor(BulkUploadProcessor):
    """Processor for bulk teacher uploads."""
    
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']
    OPTIONAL_FIELDS = [
        'phone_number', 'emergency_contact', 'gender', 'date_of_birth', 
        'blood_group', 'address', 'date_of_joining', 'employment_type',
        'salary', 'designation', 'department_code', 'role_type', 'is_hod',
        'highest_qualification', 'specialization', 'experience_years',
        'research_publications', 'certifications', 'leaves_remaining', 'employee_id'
    ]
    
    def validate_data(self):
        """Validate the uploaded data."""
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in self.data.columns]
        if missing_fields:
            raise BulkUploadError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for duplicate emails
        if self.data['email'].duplicated().any():
            duplicate_emails = self.data[self.data['email'].duplicated()]['email'].tolist()
            raise BulkUploadError(f"Duplicate emails found: {', '.join(duplicate_emails)}")
        
        # Check for existing emails in database
        existing_emails = User.objects.filter(email__in=self.data['email'].tolist()).values_list('email', flat=True)
        if existing_emails:
            raise BulkUploadError(f"Emails already exist in database: {', '.join(existing_emails)}")
        
        return True
    
    def process_teachers(self):
        """Process and create teacher records."""
        self.validate_data()
        
        for index, row in self.data.iterrows():
            try:
                with transaction.atomic():
                    # Get department if specified
                    department = None
                    if 'department_code' in row and pd.notna(row['department_code']):
                        try:
                            department = Department.objects.get(
                                code=row['department_code'], 
                                college=self.college
                            )
                        except Department.DoesNotExist:
                            self.errors.append(f"Row {index + 1}: Department with code '{row['department_code']}' not found")
                            continue
                    
                    # Create user account
                    username = row['email']
                    password = 'temp_password_123'  # Temporary password
                    
                    user = User.objects.create_user(
                        username=username,
                        email=row['email'],
                        password=password,
                        role=User.Role.TEACHER,
                        college=self.college,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        phone_number=row.get('phone_number', '')[:20],  # Truncate to 20 chars
                    )
                    
                    # Add user to college's member users
                    user.colleges.add(self.college)
                    
                    # Create teacher profile
                    teacher_data = {
                        'user': user,
                        'college': self.college,
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'email': row['email'],
                        'department': department,
                    }
                    
                    # Add employee_id if provided
                    if 'employee_id' in row and pd.notna(row['employee_id']):
                        teacher_data['employee_id'] = row['employee_id']
                    
                    # Add optional fields with length validation
                    for field in self.OPTIONAL_FIELDS:
                        if field in row and pd.notna(row[field]):
                            if field == 'department_code':
                                continue  # Already handled above
                            
                            value = row[field]
                            
                            # Apply length limits for specific fields
                            if field in ['phone_number', 'emergency_contact'] and len(str(value)) > 20:
                                value = str(value)[:20]
                            elif field == 'blood_group' and len(str(value)) > 5:
                                value = str(value)[:5]
                            
                            teacher_data[field] = value
                    
                    Teacher.objects.create(**teacher_data)
                    self.success_count += 1
                    
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors
        }


class StudentBulkUploadProcessor(BulkUploadProcessor):
    """Processor for bulk student uploads."""
    
    REQUIRED_FIELDS = ['first_name', 'last_name', 'student_number', 'academic_year']
    OPTIONAL_FIELDS = [
        'email', 'phone_number', 'birth_date', 'blood_group', 'address',
        'class_name', 'department_code', 'admission_date', 'graduation_date',
        'status', 'guardian_name', 'guardian_contact'
    ]
    
    def __init__(self, file, college, uploaded_by, teacher=None):
        super().__init__(file, college, uploaded_by)
        self.teacher = teacher
    
    def validate_data(self):
        """Validate the uploaded data."""
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in self.data.columns]
        if missing_fields:
            raise BulkUploadError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for duplicate student numbers
        if self.data['student_number'].duplicated().any():
            duplicate_numbers = self.data[self.data['student_number'].duplicated()]['student_number'].tolist()
            raise BulkUploadError(f"Duplicate student numbers found: {', '.join(duplicate_numbers)}")
        
        # Check for existing student numbers in database
        existing_numbers = Student.objects.filter(
            student_number__in=self.data['student_number'].tolist(),
            college=self.college
        ).values_list('student_number', flat=True)
        if existing_numbers:
            raise BulkUploadError(f"Student numbers already exist in database: {', '.join(existing_numbers)}")
        
        return True
    
    def process_students(self):
        """Process and create student records."""
        self.validate_data()
        
        for index, row in self.data.iterrows():
            try:
                with transaction.atomic():
                    # Get class if specified
                    class_ref = None
                    if 'class_name' in row and pd.notna(row['class_name']):
                        try:
                            class_ref = Class.objects.get(
                                name=row['class_name'],
                                college=self.college,
                                academic_year=row['academic_year']
                            )
                        except Class.DoesNotExist:
                            self.errors.append(f"Row {index + 1}: Class '{row['class_name']}' not found for academic year {row['academic_year']}")
                            continue
                    
                    # Get department if specified
                    department = None
                    if 'department_code' in row and pd.notna(row['department_code']):
                        try:
                            department = Department.objects.get(
                                code=row['department_code'],
                                college=self.college
                            )
                        except Department.DoesNotExist:
                            self.errors.append(f"Row {index + 1}: Department with code '{row['department_code']}' not found")
                            continue
                    
                    # Create user account for student
                    email = row.get('email', f"{row['student_number']}@student.local")
                    username = email
                    
                    # Check if user already exists
                    if User.objects.filter(email=email).exists():
                        self.errors.append(f"Row {index + 1}: User with email {email} already exists")
                        continue
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='temp_password_123',  # Temporary password
                        role=User.Role.STUDENT,
                        college=self.college,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        phone_number=row.get('phone_number', '')[:20],  # Truncate to 20 chars
                    )
                    
                    # Add user to college's member users
                    user.colleges.add(self.college)
                    
                    # Create student record
                    student_data = {
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'student_number': row['student_number'],
                        'academic_year': row['academic_year'],
                        'college': self.college,
                        'class_ref': class_ref,
                        'department': department,
                    }
                    
                    # Add optional fields with length validation
                    for field in self.OPTIONAL_FIELDS:
                        if field in row and pd.notna(row[field]):
                            if field in ['class_name', 'department_code']:
                                continue  # Already handled above
                            
                            value = row[field]
                            
                            # Apply length limits for specific fields
                            if field == 'phone_number' and len(str(value)) > 20:
                                value = str(value)[:20]
                            elif field == 'blood_group' and len(str(value)) > 5:
                                value = str(value)[:5]
                            elif field == 'guardian_contact' and len(str(value)) > 20:
                                value = str(value)[:20]
                            
                            student_data[field] = value
                    
                    Student.objects.create(**student_data)
                    self.success_count += 1
                    
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors
        }


class TeacherUserBulkUploadProcessor(BulkUploadProcessor):
    """Processor for bulk teacher user uploads - creates User accounts only."""
    
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']
    OPTIONAL_FIELDS = [
        'phone_number', 'emergency_contact', 'gender', 'date_of_birth', 
        'blood_group', 'address', 'date_of_joining', 'employment_type',
        'salary', 'designation', 'department_code', 'role_type', 'is_hod',
        'highest_qualification', 'specialization', 'experience_years',
        'research_publications', 'certifications', 'leaves_remaining', 'employee_id'
    ]
    
    def validate_data(self):
        """Validate the uploaded data."""
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in self.data.columns]
        if missing_fields:
            raise BulkUploadError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for duplicate emails
        if self.data['email'].duplicated().any():
            duplicate_emails = self.data[self.data['email'].duplicated()]['email'].tolist()
            raise BulkUploadError(f"Duplicate emails found: {', '.join(duplicate_emails)}")
        
        # Check for existing emails in database
        existing_emails = User.objects.filter(email__in=self.data['email'].tolist()).values_list('email', flat=True)
        if existing_emails:
            raise BulkUploadError(f"Emails already exist in database: {', '.join(existing_emails)}")
        
        return True
    
    def process_teacher_users(self):
        """Process and create teacher user records only."""
        self.validate_data()
        
        for index, row in self.data.iterrows():
            try:
                with transaction.atomic():
                    # Create user account with Teacher role
                    username = row['email']
                    password = 'temp_password_123'  # Temporary password
                    
                    user = User.objects.create_user(
                        username=username,
                        email=row['email'],
                        password=password,
                        role=User.Role.TEACHER,
                        college=self.college,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        phone_number=row.get('phone_number', '')[:20],  # Truncate to 20 chars
                        employee_id=row.get('employee_id', '')[:50],  # Truncate to 50 chars
                        designation=row.get('designation', '')[:100],  # Truncate to 100 chars
                    )
                    
                    # Add user to college's member users
                    user.colleges.add(self.college)
                    
                    self.success_count += 1
                    
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors
        }


class StudentUserBulkUploadProcessor(BulkUploadProcessor):
    """Processor for bulk student user uploads - creates User accounts only."""
    
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'student_number', 'academic_year']
    OPTIONAL_FIELDS = [
        'phone_number', 'birth_date', 'blood_group', 'address',
        'class_name', 'department_code', 'admission_date', 'graduation_date',
        'status', 'guardian_name', 'guardian_contact'
    ]
    
    def validate_data(self):
        """Validate the uploaded data."""
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in self.data.columns]
        if missing_fields:
            raise BulkUploadError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for duplicate emails
        if self.data['email'].duplicated().any():
            duplicate_emails = self.data[self.data['email'].duplicated()]['email'].tolist()
            raise BulkUploadError(f"Duplicate emails found: {', '.join(duplicate_emails)}")
        
        # Check for existing emails in database
        existing_emails = User.objects.filter(email__in=self.data['email'].tolist()).values_list('email', flat=True)
        if existing_emails:
            raise BulkUploadError(f"Emails already exist in database: {', '.join(existing_emails)}")
        
        return True
    
    def process_student_users(self):
        """Process and create student user records only."""
        self.validate_data()
        
        for index, row in self.data.iterrows():
            try:
                with transaction.atomic():
                    # Create user account with Student role
                    username = row['email']
                    password = 'temp_password_123'  # Temporary password
                    
                    user = User.objects.create_user(
                        username=username,
                        email=row['email'],
                        password=password,
                        role=User.Role.STUDENT,
                        college=self.college,
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        phone_number=row.get('phone_number', '')[:20],  # Truncate to 20 chars
                    )
                    
                    # Add user to college's member users
                    user.colleges.add(self.college)
                    
                    self.success_count += 1
                    
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors
        }


def process_teacher_user_bulk_upload(file, college, uploaded_by):
    """Process bulk teacher user upload - creates User accounts only."""
    processor = TeacherUserBulkUploadProcessor(file, college, uploaded_by)
    processor.parse_file()
    return processor.process_teacher_users()


def process_student_user_bulk_upload(file, college, uploaded_by):
    """Process bulk student user upload - creates User accounts only."""
    processor = StudentUserBulkUploadProcessor(file, college, uploaded_by)
    processor.parse_file()
    return processor.process_student_users()


# Legacy functions for backward compatibility (if needed)
def process_teacher_bulk_upload(file, college, uploaded_by):
    """Process bulk teacher upload."""
    processor = TeacherBulkUploadProcessor(file, college, uploaded_by)
    processor.parse_file()
    return processor.process_teachers()


def process_student_bulk_upload(file, college, uploaded_by, teacher=None):
    """Process bulk student upload."""
    processor = StudentBulkUploadProcessor(file, college, uploaded_by, teacher)
    processor.parse_file()
    return processor.process_students()
