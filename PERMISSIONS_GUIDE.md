# Review360 Permission System Guide

## Overview

The Review360 application implements a comprehensive role-based access control (RBAC) system with multi-tenant isolation. This guide explains the permission system, roles, and how to use them effectively.

## Architecture

### Multi-Tenant Design
- **Tenant Isolation**: Each college is a separate tenant with complete data isolation
- **Shared Schema**: All tenants share the same database schema but data is filtered by college
- **Automatic Scoping**: All queries are automatically scoped to the user's tenant context

### Permission Layers
1. **Authentication**: JWT-based authentication with OTP verification
2. **Authorization**: Role-based permissions with field-level controls
3. **Tenant Scoping**: Automatic data isolation between colleges
4. **Field-Level Security**: Fine-grained control over which fields users can modify

## Roles and Permissions

### 1. Super Admin
**Full system access across all tenants**

**Permissions:**
- Create, read, update, delete all resources
- Manage colleges and users
- Access all tenant data
- System administration

**Use Cases:**
- Platform administration
- Cross-tenant analytics
- System maintenance

### 2. College Admin
**Full access within their college(s)**

**Permissions:**
- **Classes**: Full CRUD operations
- **Students**: Full CRUD operations
- **Teachers**: Full CRUD operations
- **Departments**: Full CRUD operations
- **Subjects**: Full CRUD operations
- **Import Logs**: Read access
- **Activity Sheets**: Read access
- **Validations**: Read access
- **Follow-up Sessions**: Read, update, delete

**Use Cases:**
- College administration
- Managing academic programs
- Overseeing faculty and students

### 3. Teacher
**Limited access to assigned classes and students**

**Permissions:**
- **Classes**: Read access to assigned classes
- **Students**: Read and limited update access to their students
- **Teachers**: Read and update own profile
- **Departments**: Read access, update if HoD
- **Subjects**: Read access, update own subjects
- **Import Logs**: Create and read own imports
- **Activity Sheets**: Full CRUD operations
- **Validations**: Full CRUD operations
- **Follow-up Sessions**: Full CRUD operations

**Use Cases:**
- Teaching and student management
- Grading and validation
- Academic follow-up sessions

### 4. Student
**Read-only access to own data with limited updates**

**Permissions:**
- **Classes**: Read access to own class
- **Students**: Read and update own profile (limited fields)
- **Teachers**: Read access to teacher information
- **Departments**: Read access to own department
- **Subjects**: Read access to class subjects
- **Activity Sheets**: Create, read, update own sheets
- **Validations**: Read access to own validations
- **Follow-up Sessions**: Read access to own sessions

**Use Cases:**
- Viewing academic information
- Managing personal profile
- Submitting assignments

## Field-Level Permissions

### Student Model
**Students cannot modify:**
- `class_ref` (class assignment)
- `academic_year`
- `college`
- `department`
- `student_number`
- `status` (enrolled/graduated/dropped)

**Students can modify:**
- Personal information (name, email, phone, address)
- Guardian information
- Profile photo
- Academic preferences

### Teacher Model
**Teachers cannot modify:**
- `college`
- `employee_id`
- `department` (unless HoD)

**Teachers can modify:**
- Personal information
- Academic qualifications
- Subject assignments
- Professional details

## API Usage Examples

### Authentication
```python
# Login with OTP
POST /api/v1/iam/auth/login/
{
    "email": "user@college.edu",
    "password": "password123"
}

# Verify OTP
POST /api/v1/iam/auth/otp-verify/
{
    "email": "user@college.edu",
    "otp": "123456"
}
```

### Role-Based Access
```python
# College Admin creating a class
POST /api/v1/academics/classes/
{
    "name": "CS101",
    "academic_year": "2024-25",
    "section": "A",
    "program": "Computer Science",
    "max_students": 30
}

# Teacher viewing their classes
GET /api/v1/academics/classes/
# Automatically filtered to teacher's assigned classes

# Student updating profile (limited fields)
PATCH /api/v1/academics/students/{id}/
{
    "phone_number": "+1234567890",
    "address": "New Address"
    # Cannot modify: class_ref, academic_year, college, etc.
}
```

## Permission Classes

### RoleBasedPermission
Checks if the user's role has permission for the requested action.

```python
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [RoleBasedPermission]
```

### FieldLevelPermission
Enforces field-level access controls in serializers.

```python
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [FieldLevelPermission]
```

### TenantScopedPermission
Ensures users can only access data within their tenant scope.

```python
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [TenantScopedPermission]
```

## Middleware

### TenantMiddleware
Automatically scopes all database queries to the current user's tenant.

```python
# In settings.py
MIDDLEWARE = [
    # ... other middleware
    'iam.middleware.TenantMiddleware',
    # ... other middleware
]
```

## Database Indexes

The system includes comprehensive database indexes for optimal performance:

### Class Model
- `college_id + academic_year`
- `teacher_id + academic_year`
- `is_active`

### Student Model
- `college_id + is_active`
- `class_ref_id + academic_year`
- `department_id + academic_year`
- `student_number`
- `email`

### Teacher Model
- `college_id + is_active`
- `department_id + is_active`
- `employee_id`

## Security Features

### 1. Data Isolation
- Complete tenant isolation at the database level
- Automatic query filtering by college
- No cross-tenant data leakage

### 2. Field-Level Security
- Granular control over which fields users can modify
- Role-based field restrictions
- Validation at the serializer level

### 3. Authentication Security
- JWT tokens with configurable expiration
- OTP-based two-factor authentication
- Password reset with OTP verification

### 4. API Security
- Rate limiting on authentication endpoints
- CORS configuration for production
- Input validation and sanitization

## Best Practices

### 1. Permission Design
- Follow the principle of least privilege
- Use field-level permissions for sensitive data
- Implement proper tenant scoping

### 2. API Development
- Always use the permission classes
- Validate input at the serializer level
- Handle permission errors gracefully

### 3. Database Queries
- Use the tenant-aware querysets
- Leverage database indexes for performance
- Avoid N+1 queries with proper select_related

### 4. Testing
- Test all permission scenarios
- Verify tenant isolation
- Validate field-level restrictions

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Check user role and permissions
   - Verify tenant access
   - Review field-level restrictions

2. **Data Not Found**
   - Ensure proper tenant scoping
   - Check college assignment
   - Verify user permissions

3. **Performance Issues**
   - Check database indexes
   - Review query patterns
   - Monitor tenant scoping

### Debug Commands

```bash
# Set up permissions
python manage.py setup_permissions

# Check user permissions
python manage.py shell
>>> from iam.models import User
>>> user = User.objects.get(email='user@college.edu')
>>> print(user.get_all_permissions())
```

## Migration Guide

### From Previous Versions

1. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

2. **Set Up Permissions**
   ```bash
   python manage.py setup_permissions
   ```

3. **Update User Roles**
   ```python
   # Assign users to appropriate groups
   from django.contrib.auth.models import Group
   from iam.models import User
   
   college_admin_group = Group.objects.get(name='College Admins')
   for user in User.objects.filter(role='college_admin'):
       user.groups.add(college_admin_group)
   ```

4. **Test Permissions**
   ```bash
   python manage.py test iam.tests
   ```

## Support

For questions or issues with the permission system:

1. Check this documentation
2. Review the test cases in `iam/tests.py`
3. Examine the permission classes in `iam/permissions.py`
4. Contact the development team

---

*This guide is maintained as part of the Review360 project. Please keep it updated as the permission system evolves.*
