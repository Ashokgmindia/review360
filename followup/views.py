from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.db import transaction

from .models import FollowUpSession
from .serializers import FollowUpSessionSerializer
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission
from iam.permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission


@extend_schema_view(
    list=extend_schema(tags=["Followup"]),
    retrieve=extend_schema(tags=["Followup"]),
    create=extend_schema(tags=["Followup"]),
    update=extend_schema(tags=["Followup"]),
    partial_update=extend_schema(tags=["Followup"]),
    destroy=extend_schema(tags=["Followup"]),
)
class FollowUpSessionViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = FollowUpSession.objects.select_related("college", "student", "subject", "topic", "teacher").order_by("-session_datetime")
    serializer_class = FollowUpSessionSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["student_name", "teacher_name", "objective", "location"]
    ordering_fields = ["session_datetime", "created_at"]
    
    def get_queryset(self):
        """Override to add manual filtering."""
        queryset = super().get_queryset()
        
        # Manual filtering for status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Manual filtering for academic_year
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        # Manual filtering for student
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Manual filtering for teacher
        teacher_id = self.request.query_params.get('teacher')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)/topics')
    @extend_schema(
        tags=["Followup"],
        summary="Get student topics for follow-up sessions",
        description="Get all topics for a specific student that can have follow-up sessions scheduled",
        parameters=[
            {
                'name': 'student_id',
                'in': 'path',
                'description': 'Student ID',
                'required': True,
                'schema': {'type': 'integer'}
            }
        ],
        responses={
            200: {
                'description': 'List of student topics with progress information',
                'type': 'object',
                'properties': {
                    'student': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'email': {'type': 'string'},
                            'student_number': {'type': 'string'},
                            'class_name': {'type': 'string'}
                        }
                    },
                    'topics': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'context': {'type': 'string'},
                                'objectives': {'type': 'string'},
                                'status': {'type': 'string'},
                                'grade': {'type': 'integer'},
                                'subject_name': {'type': 'string'},
                                'teacher_name': {'type': 'string'},
                                'has_scheduled_session': {'type': 'boolean'},
                                'next_session': {'type': 'object', 'nullable': True}
                            }
                        }
                    }
                }
            }
        }
    )
    def get_student_topics(self, request, student_id=None):
        """Get all topics for a specific student that can have follow-up sessions scheduled."""
        try:
            from academics.models import Student, StudentTopicProgress
            
            student = Student.objects.get(id=student_id, is_active=True)
            
            # Get all topic progress for this student
            topic_progress = StudentTopicProgress.objects.filter(
                student=student,
                is_active=True
            ).select_related('topic', 'topic__subject', 'teacher')
            
            # Get scheduled sessions for this student
            scheduled_sessions = FollowUpSession.objects.filter(
                student=student,
                status='scheduled'
            ).select_related('topic')
            
            scheduled_topic_ids = set(session.topic.id for session in scheduled_sessions if session.topic)
            
            topics_data = []
            for progress in topic_progress:
                # Check if there's a scheduled session for this topic
                has_scheduled_session = progress.topic.id in scheduled_topic_ids
                
                # Get next scheduled session for this topic
                next_session = None
                if has_scheduled_session:
                    session = scheduled_sessions.filter(topic=progress.topic).first()
                    if session:
                        next_session = {
                            'id': session.id,
                            'session_datetime': session.session_datetime,
                            'location': session.location,
                            'objective': session.objective,
                            'status': session.status
                        }
                
                topics_data.append({
                    'id': progress.topic.id,
                    'name': progress.topic.name,
                    'context': progress.topic.context,
                    'objectives': progress.topic.objectives,
                    'status': progress.status,
                    'grade': progress.grade,
                    'subject_name': progress.topic.subject.name,
                    'teacher_name': f"{progress.teacher.first_name} {progress.teacher.last_name}" if progress.teacher else None,
                    'has_scheduled_session': has_scheduled_session,
                    'next_session': next_session
                })
            
            return Response({
                'student': {
                    'id': student.id,
                    'name': f"{student.first_name} {student.last_name}",
                    'email': student.email,
                    'student_number': student.student_number,
                    'class_name': student.class_ref.name if student.class_ref else None
                },
                'topics': topics_data
            })
            
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='schedule-from-topic-progress')
    @extend_schema(
        tags=["Followup"],
        summary="Schedule follow-up session from student topic progress",
        description="Create a new follow-up session based on student topic progress",
        request={
            'application/json': {
                'type': 'object',
                'required': ['student_topic_progress_id', 'session_datetime'],
                'properties': {
                    'student_topic_progress_id': {'type': 'integer', 'description': 'ID of the StudentTopicProgress'},
                    'session_datetime': {'type': 'string', 'format': 'date-time', 'description': 'Session date and time'},
                    'location': {'type': 'string', 'description': 'Session location'},
                    'objective': {'type': 'string', 'description': 'Session objective'},
                    'notes_for_student': {'type': 'string', 'description': 'Notes for the student'},
                    'teacher_id': {'type': 'integer', 'description': 'Teacher ID (optional)'}
                }
            }
        },
        responses={
            201: FollowUpSessionSerializer,
            400: {'description': 'Invalid data provided'},
            404: {'description': 'Student topic progress not found'}
        }
    )
    def schedule_from_topic_progress(self, request):
        """Schedule a follow-up session from student topic progress."""
        student_topic_progress_id = request.data.get('student_topic_progress_id')
        
        if not student_topic_progress_id:
            return Response(
                {"error": "student_topic_progress_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from academics.models import StudentTopicProgress
            
            student_topic_progress = StudentTopicProgress.objects.get(
                id=student_topic_progress_id,
                is_active=True
            )
            
            # Prepare data for follow-up session
            session_data = {
                'student': student_topic_progress.student.id,
                'subject': student_topic_progress.subject.id,
                'topic': student_topic_progress.topic.id,
                'session_datetime': request.data.get('session_datetime'),
                'location': request.data.get('location', ''),
                'objective': request.data.get('objective', ''),
                'notes_for_student': request.data.get('notes_for_student', ''),
                'academic_year': student_topic_progress.student.academic_year or '2024-25',
                'college': student_topic_progress.student.college.id,
            }
            
            # Add teacher if provided
            teacher_id = request.data.get('teacher_id')
            if teacher_id:
                from academics.models import Teacher
                try:
                    teacher = Teacher.objects.get(id=teacher_id, is_active=True)
                    session_data['teacher'] = teacher.id
                except Teacher.DoesNotExist:
                    return Response(
                        {"error": "Teacher not found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif student_topic_progress.teacher:
                session_data['teacher'] = student_topic_progress.teacher.id
            
            # Create the follow-up session
            serializer = self.get_serializer(data=session_data)
            if serializer.is_valid():
                session = serializer.save()
                return Response(
                    self.get_serializer(session).data, 
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": "Invalid data provided", "details": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except StudentTopicProgress.DoesNotExist:
            return Response(
                {"error": "Student topic progress not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


