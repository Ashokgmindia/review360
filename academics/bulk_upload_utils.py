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
from .models import Teacher, Student, Department, Class, StudentClassEnrollment

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
    
    REQUIRED_FIELDS = ['first_name', 'last_name']
    OPTIONAL_FIELDS = [
        'email', 'phone_number', 'birth_date', 'blood_group', 'address',
        'department_code', 'admission_date', 'graduation_date',
        'status', 'guardian_name', 'guardian_contact', 'student_number', 'academic_year'
    ]
    
    def __init__(self, file, college, uploaded_by, teacher=None, target_class=None):
        super().__init__(file, college, uploaded_by)
        self.teacher = teacher
        self.target_class = target_class
        self.existing_students_added = 0
        self.new_students_created = 0
    
    def validate_data(self):
        """Validate the uploaded data."""
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in self.data.columns]
        if missing_fields:
            raise BulkUploadError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for duplicate student numbers within the upload file (only if student_number column exists and has values)
        if 'student_number' in self.data.columns:
            # Filter out null/empty values for duplicate check
            student_numbers = self.data['student_number'].dropna()
            student_numbers = student_numbers[student_numbers != '']
            
            if not student_numbers.empty and student_numbers.duplicated().any():
                duplicate_numbers = student_numbers[student_numbers.duplicated()].tolist()
                raise BulkUploadError(f"Duplicate student numbers found in upload file: {', '.join(duplicate_numbers)}")
        
        # Note: We no longer reject existing students - they will be added to the target class
        return True
    
    def process_students(self):
        """Process and create student records or add existing students to target class."""
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
                    
                    # Generate email for student identification
                    email = row.get('email')
                    if not email or pd.isna(email) or not str(email).strip():
                        # Use student_number if available, otherwise use a generated email
                        student_number = row.get('student_number', '')
                        if student_number and not pd.isna(student_number) and str(student_number).strip():
                            email = f"{str(student_number).strip()}@student.local"
                        else:
                            email = f"student_{index + 1}@student.local"
                    else:
                        # Validate that the email looks like an actual email, not a birth date
                        email_str = str(email).strip()
                        if '@' not in email_str or email_str.count('-') > 2:  # Birth dates have many dashes
                            # This looks like a birth date, generate proper email
                            student_number = row.get('student_number', '')
                            if student_number and not pd.isna(student_number) and str(student_number).strip():
                                email = f"{str(student_number).strip()}@student.local"
                            else:
                                email = f"student_{index + 1}@student.local"
                        else:
                            email = email_str
                    
                    email = str(email).strip()
                    
                    # Check if student already exists (by email or student_number)
                    existing_student = None
                    student_number = row.get('student_number', '')
                    if student_number and pd.notna(student_number) and str(student_number).strip():
                        student_number = str(student_number).strip()
                        existing_student = Student.objects.filter(
                            student_number=student_number,
                            college=self.college
                        ).first()
                    
                    if not existing_student:
                        # Try to find by email
                        existing_student = Student.objects.filter(
                            email=email,
                            college=self.college
                        ).first()
                    
                    if existing_student:
                        # Student already exists - add them to the target class
                        if self.target_class:
                            # Check if student is already enrolled in this class
                            enrollment_exists = StudentClassEnrollment.objects.filter(
                                student=existing_student,
                                class_ref=self.target_class,
                                is_active=True
                            ).exists()
                            
                            if enrollment_exists:
                                self.errors.append(f"Row {index + 1}: Student {existing_student.first_name} {existing_student.last_name} is already enrolled in this class")
                                continue
                            
                            # Create enrollment for the student in the target class
                            print(f"DEBUG: Adding existing student {existing_student.id} to class {self.target_class.id}")
                            StudentClassEnrollment.objects.create(
                                student=existing_student,
                                class_ref=self.target_class
                            )
                            
                            # Do NOT update the primary class_ref to preserve the original class assignment
                            # The student's primary class_ref should remain unchanged as per requirements
                            print(f"DEBUG: Keeping existing student {existing_student.id} original class_ref: {existing_student.class_ref.id if existing_student.class_ref else 'None'}")
                            
                            # Only set class_ref if it's NULL, otherwise keep the original
                            if existing_student.class_ref is None:
                                print(f"DEBUG: Setting initial class_ref for student {existing_student.id} to {self.target_class.id}")
                                existing_student.class_ref = self.target_class
                                existing_student.save()
                            
                            self.existing_students_added += 1
                            self.success_count += 1
                        else:
                            self.errors.append(f"Row {index + 1}: Student {existing_student.first_name} {existing_student.last_name} already exists but no target class specified")
                            continue
                    else:
                        # Create new student
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
                            first_name=str(row['first_name']).strip(),
                            last_name=str(row['last_name']).strip(),
                            phone_number=str(row.get('phone_number', '')).strip()[:20],  # Truncate to 20 chars
                        )
                        
                        # Add user to college's member users
                        user.colleges.add(self.college)
                        
                        # Create student record with proper field mapping
                        student_data = {
                            'user': user,  # Link to the created user
                            'first_name': str(row['first_name']).strip(),
                            'last_name': str(row['last_name']).strip(),
                            'email': email,
                            'college': self.college,
                            'class_ref': self.target_class,  # Assign to target class if provided
                            'department': department,
                        }
                        print(f"DEBUG: Creating student with class_ref: {self.target_class.id if self.target_class else 'None'}")
                        
                        # Add optional fields only if they exist and are not null
                        if 'student_number' in row and pd.notna(row['student_number']) and str(row['student_number']).strip():
                            student_data['student_number'] = str(row['student_number']).strip()
                        
                        if 'academic_year' in row and pd.notna(row['academic_year']) and str(row['academic_year']).strip():
                            student_data['academic_year'] = str(row['academic_year']).strip()
                        
                        # Add optional fields with proper validation and date parsing
                        optional_field_mapping = {
                            'phone_number': 'phone_number',
                            'birth_date': 'birth_date', 
                            'blood_group': 'blood_group',
                            'address': 'address',
                            'admission_date': 'admission_date',
                            'graduation_date': 'graduation_date',
                            'status': 'status',
                            'guardian_name': 'guardian_name',
                            'guardian_contact': 'guardian_contact'
                        }
                        
                        for csv_field, model_field in optional_field_mapping.items():
                            if csv_field in row and pd.notna(row[csv_field]):
                                value = row[csv_field]
                                
                                # Handle date fields specially
                                if model_field in ['birth_date', 'admission_date', 'graduation_date']:
                                    try:
                                        # Convert to string first, then parse as date
                                        date_str = str(value).strip()
                                        if date_str:
                                            # Try to parse the date - handle different formats
                                            if '-' in date_str:
                                                # Assume YYYY-MM-DD format
                                                from datetime import datetime
                                                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                                                student_data[model_field] = parsed_date
                                            else:
                                                # Try pandas to_datetime for other formats
                                                parsed_date = pd.to_datetime(value).date()
                                                student_data[model_field] = parsed_date
                                    except (ValueError, TypeError) as e:
                                        self.errors.append(f"Row {index + 1}: Invalid date format for {csv_field}: {value}")
                                        continue
                                else:
                                    # Handle non-date fields
                                    value = str(value).strip()
                                    
                                    # Apply length limits for specific fields
                                    if model_field == 'phone_number' and len(value) > 20:
                                        value = value[:20]
                                    elif model_field == 'blood_group' and len(value) > 5:
                                        value = value[:5]
                                    elif model_field == 'guardian_contact' and len(value) > 20:
                                        value = value[:20]
                                    
                                    student_data[model_field] = value
                        
                        new_student = Student.objects.create(**student_data)
                        
                        # Create enrollment for the new student in the target class
                        if self.target_class:
                            print(f"DEBUG: Creating enrollment for student {new_student.id} in class {self.target_class.id}")
                            StudentClassEnrollment.objects.create(
                                student=new_student,
                                class_ref=self.target_class
                            )
                        
                        self.new_students_created += 1
                        self.success_count += 1
                    
            except Exception as e:
                self.errors.append(f"Row {index + 1}: {str(e)}")
        
        return {
            'success_count': self.success_count,
            'new_students_created': self.new_students_created,
            'existing_students_added': self.existing_students_added,
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


def process_student_bulk_upload(file, college, uploaded_by, teacher=None, target_class=None):
    """Process bulk student upload."""
    processor = StudentBulkUploadProcessor(file, college, uploaded_by, teacher, target_class)
    processor.parse_file()
    return processor.process_students()
