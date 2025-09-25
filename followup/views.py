from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.db import transaction
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
import logging

from .models import FollowUpSession, Location, Objective
from .serializers import FollowUpSessionSerializer, LocationSerializer, ObjectiveSerializer
from .google_calendar_service import google_calendar_service
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission
from iam.permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Followup"],
        summary="List follow-up sessions",
        description="Get a list of all follow-up sessions with automatic Google Calendar and email integration"
    ),
    retrieve=extend_schema(
        tags=["Followup"],
        summary="Get session details",
        description="Retrieve details of a specific follow-up session"
    ),
    create=extend_schema(
        tags=["Followup"],
        summary="Create session with automatic integration",
        description="Create a new follow-up session with automatic Google Calendar event creation and email invitations. Location and objective should be provided as IDs.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'college': {'type': 'integer', 'description': 'College ID'},
                    'student': {'type': 'integer', 'description': 'Student ID'},
                    'subject': {'type': 'integer', 'description': 'Subject ID'},
                    'topic': {'type': 'integer', 'description': 'Topic ID'},
                    'teacher': {'type': 'integer', 'description': 'Teacher ID'},
                    'location': {'type': 'integer', 'description': 'Location ID (from /api/v1/followup/locations/)'},
                    'objective': {'type': 'integer', 'description': 'Objective ID (from /api/v1/followup/objectives/)'},
                    'session_datetime': {'type': 'string', 'format': 'date-time', 'description': 'Session date and time'},
                    'notes_for_student': {'type': 'string', 'description': 'Notes for the student'},
                    'status': {'type': 'string', 'enum': ['scheduled', 'completed', 'cancelled', 'rescheduled'], 'default': 'scheduled'},
                    'google_calendar_event_id': {'type': 'string', 'description': 'Google Calendar event ID'},
                    'add_to_google_calendar': {'type': 'boolean', 'default': False, 'description': 'Whether to add to Google Calendar'},
                    'invite_student': {'type': 'boolean', 'default': False, 'description': 'Whether to send email invitation'},
                    'automatic_reminder': {'type': 'boolean', 'default': False, 'description': 'Whether to send automatic reminder'},
                    'academic_year': {'type': 'string', 'description': 'Academic year'}
                },
                'required': ['college', 'student', 'subject', 'topic', 'teacher', 'session_datetime', 'academic_year']
            }
        }
    ),
    update=extend_schema(
        tags=["Followup"],
        summary="Update session with automatic integration",
        description="Update a follow-up session with automatic Google Calendar and email integration"
    ),
    partial_update=extend_schema(
        tags=["Followup"],
        summary="Partially update session",
        description="Partially update a follow-up session with automatic Google Calendar and email integration"
    ),
    destroy=extend_schema(
        tags=["Followup"],
        summary="Delete session",
        description="Delete a follow-up session and automatically remove associated Google Calendar events"
    ),
)
@extend_schema(
    tags=["Followup"],
    operation_id="followup_sessions"
)
class FollowUpSessionViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = FollowUpSession.objects.select_related("college", "student", "subject", "topic", "teacher", "location", "objective").order_by("-session_datetime")
    serializer_class = FollowUpSessionSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["student_name", "teacher_name", "objective_title", "location_name"]
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
        operation_id="followup_get_student_topics",
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
            ).select_related('topic', 'topic__subject', 'subject')
            
            # Get scheduled sessions for this student
            scheduled_sessions = FollowUpSession.objects.filter(
                student=student,
                status='scheduled'
            ).select_related('topic')
            
            scheduled_topic_ids = set(session.topic.id for session in scheduled_sessions if session.topic)
            
            # Get teacher information for each subject
            from academics.models import StudentSubject
            student_subjects = StudentSubject.objects.filter(
                student=student,
                is_active=True
            ).select_related('teacher', 'subject')
            
            # Create a mapping of subject_id to teacher
            subject_teacher_map = {}
            for student_subject in student_subjects:
                if student_subject.teacher:
                    subject_teacher_map[student_subject.subject.id] = student_subject.teacher
            
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
                
                # Get teacher name from the mapping
                teacher = subject_teacher_map.get(progress.subject.id)
                teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else None
                
                topics_data.append({
                    'id': progress.topic.id,
                    'name': progress.topic.name,
                    'context': progress.topic.context,
                    'objectives': progress.topic.objectives,
                    'status': progress.status,
                    'grade': progress.grade,
                    'subject_name': progress.topic.subject.name,
                    'teacher_name': teacher_name,
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
    
    @action(detail=False, methods=['get'], url_path='session-options')
    @extend_schema(
        tags=["Followup"],
        operation_id="followup_get_session_options",
        summary="Get session creation options",
        description="Get available locations and objectives for creating follow-up sessions",
        responses={
            200: {
                'description': 'Available locations and objectives for session creation',
                'type': 'object',
                'properties': {
                    'locations': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'description': {'type': 'string'},
                                'is_active': {'type': 'boolean'}
                            }
                        }
                    },
                    'objectives': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'title': {'type': 'string'},
                                'description': {'type': 'string'},
                                'is_active': {'type': 'boolean'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get_session_options(self, request):
        """Get available locations and objectives for creating follow-up sessions."""
        # Get user's college
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user's college
        college = getattr(user, "college", None)
        if not college:
            return Response(
                {"error": "College not found for user"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active locations for the college
        locations = Location.objects.filter(college=college, is_active=True).order_by('name')
        locations_data = [
            {
                'id': location.id,
                'name': location.name,
                'description': location.description,
                'is_active': location.is_active
            }
            for location in locations
        ]
        
        # Get active objectives for the college
        objectives = Objective.objects.filter(college=college, is_active=True).order_by('title')
        objectives_data = [
            {
                'id': objective.id,
                'title': objective.title,
                'description': objective.description,
                'is_active': objective.is_active
            }
            for objective in objectives
        ]
        
        return Response({
            'locations': locations_data,
            'objectives': objectives_data
        })
    
    def perform_create(self, serializer):
        """Override create to handle Google Calendar integration and email invitations."""
        with transaction.atomic():
            instance = serializer.save()
            
            # Handle Google Calendar integration automatically
            if instance.add_to_google_calendar:
                try:
                    self._create_google_calendar_event(instance)
                    logger.info(f"Google Calendar event created for session {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to create Google Calendar event for session {instance.id}: {e}")
            
            # Send email invitation automatically if requested
            if instance.invite_student and instance.student and instance.student.email:
                try:
                    self._send_email_invitation(instance)
                    logger.info(f"Email invitation sent for session {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to send email invitation for session {instance.id}: {e}")
    
    def perform_update(self, serializer):
        """Override update to handle Google Calendar integration and email invitations."""
        with transaction.atomic():
            instance = serializer.save()
            
            # Handle Google Calendar integration automatically
            if instance.add_to_google_calendar:
                if instance.google_calendar_event_id:
                    # Update existing event
                    try:
                        self._update_google_calendar_event(instance)
                        logger.info(f"Google Calendar event updated for session {instance.id}")
                    except Exception as e:
                        logger.error(f"Failed to update Google Calendar event for session {instance.id}: {e}")
                else:
                    # Create new event
                    try:
                        self._create_google_calendar_event(instance)
                        logger.info(f"Google Calendar event created for session {instance.id}")
                    except Exception as e:
                        logger.error(f"Failed to create Google Calendar event for session {instance.id}: {e}")
            elif not instance.add_to_google_calendar and instance.google_calendar_event_id:
                # Remove from Google Calendar
                try:
                    self._delete_google_calendar_event(instance)
                    logger.info(f"Google Calendar event deleted for session {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to delete Google Calendar event for session {instance.id}: {e}")
            
            # Send email invitation automatically if requested
            if instance.invite_student and instance.student and instance.student.email:
                try:
                    self._send_email_invitation(instance)
                    logger.info(f"Email invitation sent for session {instance.id}")
                except Exception as e:
                    logger.error(f"Failed to send email invitation for session {instance.id}: {e}")
    
    def perform_destroy(self, instance):
        """Override destroy to handle Google Calendar cleanup."""
        with transaction.atomic():
            # Delete Google Calendar event if it exists
            if instance.google_calendar_event_id:
                self._delete_google_calendar_event(instance)
            
            instance.delete()
    
    def _create_google_calendar_event(self, session):
        """Create Google Calendar event for the session."""
        try:
            session_data = self._prepare_session_data(session)
            event_id = google_calendar_service.create_event(session_data)
            
            if event_id:
                session.google_calendar_event_id = event_id
                session.save(update_fields=['google_calendar_event_id'])
                logger.info(f"Created Google Calendar event {event_id} for session {session.id}")
            else:
                logger.warning(f"Failed to create Google Calendar event for session {session.id}")
                
        except Exception as e:
            logger.error(f"Error creating Google Calendar event for session {session.id}: {e}")
    
    def _update_google_calendar_event(self, session):
        """Update Google Calendar event for the session."""
        try:
            session_data = self._prepare_session_data(session)
            success = google_calendar_service.update_event(session.google_calendar_event_id, session_data)
            
            if success:
                logger.info(f"Updated Google Calendar event {session.google_calendar_event_id} for session {session.id}")
            else:
                logger.warning(f"Failed to update Google Calendar event for session {session.id}")
                
        except Exception as e:
            logger.error(f"Error updating Google Calendar event for session {session.id}: {e}")
    
    def _delete_google_calendar_event(self, session):
        """Delete Google Calendar event for the session."""
        try:
            success = google_calendar_service.delete_event(session.google_calendar_event_id)
            
            if success:
                logger.info(f"Deleted Google Calendar event {session.google_calendar_event_id} for session {session.id}")
            else:
                logger.warning(f"Failed to delete Google Calendar event for session {session.id}")
                
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event for session {session.id}: {e}")
    
    def _send_email_invitation(self, session):
        """Send email invitation for the session."""
        try:
            session_data = self._prepare_session_data(session)
            success = google_calendar_service.send_email_invitation(session_data, session.google_calendar_event_id)
            
            if success:
                logger.info(f"Sent email invitation for session {session.id}")
            else:
                logger.warning(f"Failed to send email invitation for session {session.id}")
                
        except Exception as e:
            logger.error(f"Error sending email invitation for session {session.id}: {e}")
    
    def _prepare_session_data(self, session):
        """Prepare session data for Google Calendar and email services."""
        session_data = {
            'student_name': session.student_name,
            'student_email': session.student.email if session.student else None,
            'teacher_name': session.teacher_name,
            'teacher_email': session.teacher.email if session.teacher else None,
            'subject_name': session.subject_name,
            'topic_name': session.topic_name,
            'session_datetime': session.session_datetime,
            'location': session.location,
            'objective': session.objective,
            'notes_for_student': session.notes_for_student,
            'send_invitations': session.invite_student,
        }
        return session_data
    


@extend_schema_view(
    list=extend_schema(
        tags=["Followup"],
        summary="List locations",
        description="Get a list of all locations for follow-up sessions"
    ),
    retrieve=extend_schema(
        tags=["Followup"],
        summary="Get location details",
        description="Retrieve details of a specific location"
    ),
    create=extend_schema(
        tags=["Followup"],
        summary="Create location",
        description="Create a new location for follow-up sessions"
    ),
    update=extend_schema(
        tags=["Followup"],
        summary="Update location",
        description="Update a location"
    ),
    partial_update=extend_schema(
        tags=["Followup"],
        summary="Partially update location",
        description="Partially update a location"
    ),
    destroy=extend_schema(
        tags=["Followup"],
        summary="Delete location",
        description="Delete a location"
    ),
)
class LocationViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet for managing locations."""
    queryset = Location.objects.select_related("college").order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


@extend_schema_view(
    list=extend_schema(
        tags=["Followup"],
        summary="List objectives",
        description="Get a list of all objectives for follow-up sessions"
    ),
    retrieve=extend_schema(
        tags=["Followup"],
        summary="Get objective details",
        description="Retrieve details of a specific objective"
    ),
    create=extend_schema(
        tags=["Followup"],
        summary="Create objective",
        description="Create a new objective for follow-up sessions"
    ),
    update=extend_schema(
        tags=["Followup"],
        summary="Update objective",
        description="Update an objective"
    ),
    partial_update=extend_schema(
        tags=["Followup"],
        summary="Partially update objective",
        description="Partially update an objective"
    ),
    destroy=extend_schema(
        tags=["Followup"],
        summary="Delete objective",
        description="Delete an objective"
    ),
)
class ObjectiveViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    """ViewSet for managing objectives."""
    queryset = Objective.objects.select_related("college").order_by("title")
    serializer_class = ObjectiveSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]


def schedule_session_view(request):
    """
    View to display the scheduling form.
    """
    return render(request, 'followup/schedule_session.html')
    
