"""
Separate bulk upload views for creating User accounts only.
These APIs are completely separate from the Teacher/Student model operations.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import AutoSchema
from django.db import transaction
from rest_framework import serializers

from .bulk_upload_utils import process_teacher_user_bulk_upload, process_student_user_bulk_upload, BulkUploadError
from .models import Teacher, Student
from rest_framework.permissions import IsAuthenticated


class BulkUploadResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())


@extend_schema(
    tags=["Academics"],
    summary="Bulk upload teacher users",
    description="Upload teacher users in bulk via Excel, CSV, or JSON file. Requires 'academics.add_teacher' permission. Creates User accounts with Teacher role only.",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Excel (.xlsx), CSV (.csv), or JSON (.json) file containing teacher data'
                }
            },
            'required': ['file']
        }
    },
    responses={
        201: BulkUploadResponseSerializer,
        400: serializers.Serializer,
        403: serializers.Serializer,
        500: serializers.Serializer
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_teacher_users(request):
    """Bulk upload teacher users from file."""
    user = request.user
    
    # Check if user has permission to add teachers using role-based permissions
    from iam.permissions import RoleBasedPermission
    permission_checker = RoleBasedPermission()
    
    # Create a mock view to check permissions
    class MockView:
        queryset = Teacher.objects.all()
        action = 'create'
    
    if not permission_checker.has_permission(request, MockView()):
        return Response(
            {"error": "You don't have permission to add teachers. Contact your administrator."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get the file from request
    if 'file' not in request.FILES:
        return Response(
            {"error": "No file provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Get college from user
    college = user.college
    if not college:
        return Response(
            {"error": "User is not associated with any college."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = process_teacher_user_bulk_upload(file, college, user)
        
        return Response({
            "message": f"Bulk upload completed. {result['success_count']} teacher users created successfully.",
            "success_count": result['success_count'],
            "error_count": result['error_count'],
            "errors": result['errors']
        }, status=status.HTTP_201_CREATED)
            
    except BulkUploadError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=["Academics"],
    summary="Bulk upload student users",
    description="Upload student users in bulk via Excel, CSV, or JSON file. Requires 'academics.add_student' permission. Creates User accounts with Student role only.",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Excel (.xlsx), CSV (.csv), or JSON (.json) file containing student data'
                }
            },
            'required': ['file']
        }
    },
    responses={
        201: BulkUploadResponseSerializer,
        400: serializers.Serializer,
        403: serializers.Serializer,
        500: serializers.Serializer
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_student_users(request):
    """Bulk upload student users from file."""
    user = request.user
    
    # Check if user has permission to add students using role-based permissions
    from iam.permissions import RoleBasedPermission
    permission_checker = RoleBasedPermission()
    
    # Create a mock view to check permissions
    class MockView:
        queryset = Student.objects.all()
        action = 'create'
    
    if not permission_checker.has_permission(request, MockView()):
        return Response(
            {"error": "You don't have permission to add students. Contact your administrator."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get the file from request
    if 'file' not in request.FILES:
        return Response(
            {"error": "No file provided."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Get college from user
    college = user.college
    if not college:
        return Response(
            {"error": "User is not associated with any college."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = process_student_user_bulk_upload(file, college, user)
        
        return Response({
            "message": f"Bulk upload completed. {result['success_count']} student users created successfully.",
            "success_count": result['success_count'],
            "error_count": result['error_count'],
            "errors": result['errors']
        }, status=status.HTTP_201_CREATED)
            
    except BulkUploadError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
