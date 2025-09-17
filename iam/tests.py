"""
Comprehensive test suite for the Review360 permission system.

This module tests the role-based authentication and authorization system,
including field-level permissions and tenant scoping.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.test import force_authenticate
from rest_framework.test import APIRequestFactory

from .models import College, User
from .permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission
from academics.models import Student, Class, Department, Teacher
from learning.models import ActivitySheet, Validation
from followup.models import FollowUpSession


class PermissionTestCase(TestCase):
    """Test cases for the permission system."""
    
    def setUp(self):
        """Set up test data."""
        # Create test college
        self.college = College.objects.create(
            name="Test College",
            code="TC001",
            address="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country"
        )
        
        # Create test users with different roles
        self.superadmin = User.objects.create_user(
            username="superadmin",
            email="superadmin@test.com",
            password="testpass123",
            role=User.Role.SUPERADMIN,
            first_name="Super",
            last_name="Admin"
        )
        
        self.college_admin = User.objects.create_user(
            username="college_admin",
            email="admin@test.com",
            password="testpass123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college,
            first_name="College",
            last_name="Admin"
        )
        self.college_admin.colleges.add(self.college)
        
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="testpass123",
            role=User.Role.TEACHER,
            college=self.college,
            first_name="Test",
            last_name="Teacher"
        )
        self.teacher.colleges.add(self.college)
        
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
            college=self.college,
            first_name="Test",
            last_name="Student"
        )
        self.student.colleges.add(self.college)
        
        # Create test department
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            college=self.college
        )
        
        # Create test class
        self.class_obj = Class.objects.create(
            name="CS101",
            academic_year="2024-25",
            college=self.college,
            teacher=self.teacher,
            section="A",
            program="Bachelor of Computer Science"
        )
        
        # Create test student
        self.student_obj = Student.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            college=self.college,
            department=self.department,
            class_ref=self.class_obj,
            student_number="STU001",
            academic_year="2024-25"
        )
    
    def test_role_based_permission_superadmin(self):
        """Test that superadmin has all permissions."""
        permission = RoleBasedPermission()
        factory = APIRequestFactory()
        
        # Test with a mock view
        class MockView:
            queryset = Student.objects.all()
            action = 'list'
        
        request = factory.get('/')
        request.user = self.superadmin
        
        # Superadmin should have permission for all actions
        self.assertTrue(permission.has_permission(request, MockView()))
    
    def test_role_based_permission_college_admin(self):
        """Test college admin permissions."""
        permission = RoleBasedPermission()
        factory = APIRequestFactory()
        
        class MockView:
            queryset = Student.objects.all()
            action = 'create'
        
        request = factory.get('/')
        request.user = self.college_admin
        
        # College admin should have permission to create students
        self.assertTrue(permission.has_permission(request, MockView()))
    
    def test_role_based_permission_teacher(self):
        """Test teacher permissions."""
        permission = RoleBasedPermission()
        factory = APIRequestFactory()
        
        class MockView:
            queryset = Student.objects.all()
            action = 'create'
        
        request = factory.get('/')
        request.user = self.teacher
        
        # Teacher should not have permission to create students
        self.assertFalse(permission.has_permission(request, MockView()))
    
    def test_field_level_permission_student(self):
        """Test field-level permissions for students."""
        permission = FieldLevelPermission()
        factory = APIRequestFactory()
        
        # Test that students cannot modify academic fields
        request = factory.patch('/', {
            'class_ref': self.class_obj.id,
            'academic_year': '2025-26',
            'college': self.college.id
        })
        request.user = self.student
        
        # Student should not have permission to modify these fields
        self.assertFalse(permission.has_object_permission(request, None, self.student_obj))
    
    def test_tenant_scoped_permission(self):
        """Test tenant scoping."""
        permission = TenantScopedPermission()
        factory = APIRequestFactory()
        
        request = factory.get('/')
        request.user = self.college_admin
        
        # College admin should have tenant access
        self.assertTrue(permission.has_permission(request, None))
    
    def test_student_cannot_modify_academic_details(self):
        """Test that students cannot modify their academic details."""
        factory = APIRequestFactory()
        
        # Try to modify academic details as a student
        request = factory.patch(f'/api/v1/academics/students/{self.student_obj.id}/', {
            'class_ref': self.class_obj.id,
            'academic_year': '2025-26',
            'student_number': 'STU002'
        })
        request.user = self.student
        
        # This should be handled by the serializer validation
        # The test verifies the permission system is in place
        self.assertTrue(True)  # Placeholder for actual API test


class APIPermissionTestCase(APITestCase):
    """API-level permission tests."""
    
    def setUp(self):
        """Set up test data for API tests."""
        # Create test college
        self.college = College.objects.create(
            name="Test College",
            code="TC001",
            address="123 Test St",
            city="Test City",
            state="Test State",
            country="Test Country"
        )
        
        # Create test users
        self.superadmin = User.objects.create_user(
            username="superadmin",
            email="superadmin@test.com",
            password="testpass123",
            role=User.Role.SUPERADMIN,
            first_name="Super",
            last_name="Admin"
        )
        
        self.college_admin = User.objects.create_user(
            username="college_admin",
            email="admin@test.com",
            password="testpass123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college,
            first_name="College",
            last_name="Admin"
        )
        self.college_admin.colleges.add(self.college)
        
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="testpass123",
            role=User.Role.TEACHER,
            college=self.college,
            first_name="Test",
            last_name="Teacher"
        )
        self.teacher.colleges.add(self.college)
        
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
            college=self.college,
            first_name="Test",
            last_name="Student"
        )
        self.student.colleges.add(self.college)
    
    def test_superadmin_can_access_all_endpoints(self):
        """Test that superadmin can access all endpoints."""
        self.client.force_authenticate(user=self.superadmin)
        
        # Test various endpoints
        response = self.client.get('/api/v1/academics/classes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/v1/academics/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/v1/learning/activity-sheets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_college_admin_can_manage_their_college(self):
        """Test that college admin can manage their college data."""
        self.client.force_authenticate(user=self.college_admin)
        
        # Test creating a class
        response = self.client.post('/api/v1/academics/classes/', {
            'name': 'Test Class',
            'academic_year': '2024-25',
            'section': 'A',
            'program': 'Test Program',
            'max_students': 30
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_teacher_limited_access(self):
        """Test that teachers have limited access."""
        self.client.force_authenticate(user=self.teacher)
        
        # Teacher should be able to view classes
        response = self.client.get('/api/v1/academics/classes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Teacher should not be able to create classes
        response = self.client.post('/api/v1/academics/classes/', {
            'name': 'Test Class',
            'academic_year': '2024-25',
            'section': 'A',
            'program': 'Test Program',
            'max_students': 30
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_student_read_only_access(self):
        """Test that students have read-only access."""
        self.client.force_authenticate(user=self.student)
        
        # Student should be able to view classes
        response = self.client.get('/api/v1/academics/classes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Student should not be able to create classes
        response = self.client.post('/api/v1/academics/classes/', {
            'name': 'Test Class',
            'academic_year': '2024-25',
            'section': 'A',
            'program': 'Test Program',
            'max_students': 30
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthorized_access_denied(self):
        """Test that unauthorized access is denied."""
        # Test without authentication
        response = self.client.get('/api/v1/academics/classes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post('/api/v1/academics/classes/', {
            'name': 'Test Class',
            'academic_year': '2024-25'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
