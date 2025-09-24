"""
Simple test to verify the API schema is working correctly.
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from academics.models import Class, Student, Teacher, Department, StudentSubject
from learning.models import Subject, Topic
from iam.models import College

User = get_user_model()

class SchemaVerificationTest(APITestCase):
    def setUp(self):
        """Set up test data."""
        # Create college
        self.college = College.objects.create(
            name="Test College",
            code="TC",
            address="Test Address"
        )
        
        # Create department
        self.department = Department.objects.create(
            name="Computer Science",
            code="CS",
            college=self.college
        )
        
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            username="teacher@test.com",
            email="teacher@test.com",
            password="testpass123",
            role=User.Role.TEACHER,
            college=self.college
        )
        
        # Create teacher
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            college=self.college,
            first_name="John",
            last_name="Doe",
            email="teacher@test.com",
            department=self.department,
            employee_id="T001"
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            name="Python Programming",
            code="CS101",
            department=self.department,
            college=self.college,
            semester=1,
            credits=3
        )
        
        # Create class
        self.class_obj = Class.objects.create(
            name="CS-1A",
            academic_year="2024-25",
            college=self.college,
            teacher=self.teacher,
            section="A",
            program="Computer Science",
            semester=1
        )
        
        # Create student
        self.student = Student.objects.create(
            first_name="Alice",
            last_name="Johnson",
            email="alice@test.com",
            class_ref=self.class_obj,
            college=self.college,
            department=self.department,
            student_number="S001"
        )
        
        # Create topic
        self.topic = Topic.objects.create(
            name="Introduction to Python",
            context="Basic Python concepts",
            objectives="Learn Python basics",
            subject=self.subject,
            qns1_text="Question 1",
            qns2_text="Question 2",
            qns3_text="Question 3",
            qns4_text="Question 4"
        )

    def test_put_endpoint_accepts_correct_schema(self):
        """Test that the PUT endpoint accepts the correct schema with subjects and topics."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = f'/api/academics/students/class/{self.class_obj.id}/student/{self.student.id}/subjects/'
        
        # Test data with correct schema (subjects and topics)
        correct_data = {
            "subjects": [
                {
                    "subject_id": self.subject.id,
                    "teacher_id": self.teacher.id,
                    "is_active": True,
                    "topics": [
                        {
                            "id": self.topic.id,
                            "status": "in_progress",
                            "grade": 5,
                            "comments_and_recommendations": "Good progress",
                            "qns1_checked": True,
                            "qns2_checked": True,
                            "qns3_checked": False,
                            "qns4_checked": False
                        }
                    ]
                }
            ]
        }
        
        response = self.client.put(url, correct_data, format='json')
        
        # Should succeed with correct schema
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('updated_assignments', data)
        self.assertIn('updated_topics', data)

    def test_put_endpoint_rejects_incorrect_schema(self):
        """Test that the PUT endpoint rejects incorrect schema (student profile data)."""
        self.client.force_authenticate(user=self.teacher_user)
        
        url = f'/api/academics/students/class/{self.class_obj.id}/student/{self.student.id}/subjects/'
        
        # Test data with incorrect schema (student profile data)
        incorrect_data = {
            "first_name": "Updated Name",
            "last_name": "Updated Last Name",
            "email": "updated@example.com",
            "phone_number": "1234567890",
            "birth_date": "2000-01-01",
            "blood_group": "A+",
            "address": "Updated Address",
            "profile_photo": "photo.jpg",
            "class_ref": self.class_obj.id,
            "academic_year": "2024-25",
            "college": self.college.id,
            "department": self.department.id,
            "student_number": "S001",
            "admission_date": "2024-01-01",
            "graduation_date": "2027-01-01",
            "status": "enrolled",
            "guardian_name": "Guardian Name",
            "guardian_contact": "9876543210",
            "is_active": True,
            "metadata": "{}"
        }
        
        response = self.client.put(url, incorrect_data, format='json')
        
        # Should fail with incorrect schema
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check error message
        data = response.json()
        self.assertIn('error', data)

if __name__ == '__main__':
    print("Schema Verification Test")
    print("This test verifies that the API accepts the correct schema and rejects incorrect schema.")
    print("Run with: python manage.py test test_schema_verification")
