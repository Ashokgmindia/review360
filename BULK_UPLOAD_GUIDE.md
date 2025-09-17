# Bulk Upload Guide

This guide explains how to use the bulk upload functionality for creating User accounts in the Review360 system.

## Overview

The bulk upload feature allows you to create multiple User accounts at once using Excel (.xlsx), CSV (.csv), or JSON (.json) files. This feature creates User accounts with appropriate roles (Teacher or Student) but does NOT create Teacher or Student model records.

## Teacher User Bulk Upload

### Who Can Upload
- **Users with `academics.add_teacher` permission** can perform bulk teacher user uploads

### API Endpoint
```
POST /api/v1/academics/bulk-upload/teacher-users/
```

### Required Fields
- `first_name` - Teacher's first name
- `last_name` - Teacher's last name  
- `email` - Teacher's email address (must be unique)
- `employee_id` - Teacher's employee ID (must be unique within college)

### Optional Fields
- `phone_number` - Contact phone number
- `emergency_contact` - Emergency contact number
- `gender` - Gender (Male/Female/Other)
- `date_of_birth` - Date of birth (YYYY-MM-DD format)
- `blood_group` - Blood group
- `address` - Physical address
- `date_of_joining` - Date of joining (YYYY-MM-DD format)
- `employment_type` - full-time/part-time/visiting
- `salary` - Salary amount
- `designation` - Job designation
- `department_code` - Department code (must exist in the college)
- `role_type` - Role type (default: Teaching)
- `is_hod` - Is Head of Department (true/false)
- `highest_qualification` - Highest educational qualification
- `specialization` - Area of specialization
- `experience_years` - Years of experience
- `research_publications` - Number of research publications
- `certifications` - Professional certifications
- `leaves_remaining` - Remaining leave days

### Sample CSV Format
```csv
first_name,last_name,email,employee_id,phone_number,emergency_contact,gender,date_of_birth,blood_group,address,date_of_joining,employment_type,salary,designation,department_code,role_type,is_hod,highest_qualification,specialization,experience_years,research_publications,certifications,leaves_remaining
John,Doe,john.doe@college.edu,EMP001,1234567890,9876543210,Male,1985-05-15,A+,123 Main St,2023-01-15,full-time,50000,Professor,CS,Teaching,false,PhD,Computer Science,10,5,Microsoft Certified,20
```

## Student User Bulk Upload

### Who Can Upload
- **Users with `academics.add_student` permission** can perform bulk student user uploads

### API Endpoint
```
POST /api/v1/academics/bulk-upload/student-users/
```

### Required Fields
- `first_name` - Student's first name
- `last_name` - Student's last name
- `email` - Student's email address (must be unique)
- `student_number` - Student's unique number (must be unique within college)
- `academic_year` - Academic year (e.g., 2023-24)

### Optional Fields
- `phone_number` - Contact phone number
- `birth_date` - Date of birth (YYYY-MM-DD format)
- `blood_group` - Blood group
- `address` - Physical address
- `class_name` - Class name (must exist in the college for the academic year)
- `department_code` - Department code (must exist in the college)
- `admission_date` - Date of admission (YYYY-MM-DD format)
- `graduation_date` - Expected graduation date (YYYY-MM-DD format)
- `status` - Student status (enrolled/graduated/dropped)
- `guardian_name` - Guardian's name
- `guardian_contact` - Guardian's contact number

### Sample CSV Format
```csv
first_name,last_name,email,student_number,academic_year,phone_number,birth_date,blood_group,address,class_name,department_code,admission_date,graduation_date,status,guardian_name,guardian_contact
Alice,Williams,alice.williams@student.edu,STU001,2023-24,1111111111,2005-03-15,A+,101 Student St,Computer Science 101,CS,2023-08-15,,enrolled,Robert Williams,2222222222
```

## File Format Support

### Excel (.xlsx)
- Use the first row as column headers
- Data should start from the second row
- Empty rows will be ignored

### CSV (.csv)
- First row must contain column headers
- Use comma as delimiter
- Enclose text fields in quotes if they contain commas

### JSON (.json)
- Array of objects format
- Each object represents one record
- Field names must match the required/optional field names

## Error Handling

The system provides detailed error reporting:

- **Validation Errors**: Missing required fields, invalid data formats
- **Duplicate Errors**: Email addresses or IDs that already exist
- **Reference Errors**: Department codes or class names that don't exist
- **Row-level Errors**: Specific errors for each row with row numbers

## Response Format

```json
{
    "message": "Bulk upload completed. 5 teachers created successfully.",
    "success_count": 5,
    "error_count": 2,
    "errors": [
        "Row 3: Department with code 'INVALID' not found",
        "Row 7: Email already exists in database"
    ]
}
```

## Best Practices

1. **Use Sample Templates**: Download and use the provided sample templates
2. **Validate Data First**: Check your data for duplicates and format issues
3. **Test with Small Files**: Start with a small batch to test the format
4. **Check Department/Class Codes**: Ensure all referenced codes exist in the system
5. **Backup Data**: Always backup existing data before bulk operations
6. **Review Errors**: Carefully review error messages and fix issues before re-uploading

## Security Notes

- All uploaded files are stored securely
- Temporary passwords are generated for new user accounts
- Users should change their passwords on first login
- File uploads are restricted by user permissions and college scope

## Troubleshooting

### Common Issues

1. **"Missing required fields"**: Ensure all required columns are present
2. **"Email already exists"**: Check for duplicate email addresses in your file
3. **"Department not found"**: Verify department codes exist in the system
4. **"Class not found"**: Ensure class names and academic years match existing records
5. **"Permission denied"**: Verify you have the correct role for the upload operation

### Getting Help

If you encounter issues not covered in this guide:
1. Check the error messages in the API response
2. Verify your file format matches the sample templates
3. Contact your system administrator for permission issues
4. Review the API documentation for detailed field requirements
