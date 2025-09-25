"""
Celery tasks for follow-up sessions.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .models import FollowUpSession
from .google_calendar_service import google_calendar_service

logger = logging.getLogger(__name__)


@shared_task
def send_session_reminders():
    """
    Send reminders for sessions scheduled 24 hours from now.
    This task should be run periodically (e.g., every hour).
    """
    try:
        # Calculate the time range for sessions starting in 24 hours
        now = timezone.now()
        reminder_time = now + timedelta(hours=24)
        
        # Find sessions that need reminders (within the next hour)
        sessions = FollowUpSession.objects.filter(
            session_datetime__gte=reminder_time,
            session_datetime__lt=reminder_time + timedelta(hours=1),
            status='scheduled',
            automatic_reminder=True,
            student__isnull=False
        ).select_related('student', 'teacher', 'subject', 'topic')
        
        sent_count = 0
        for session in sessions:
            try:
                # Prepare session data for reminder email
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
                }
                
                # Send reminder email
                if session_data['student_email']:
                    success = google_calendar_service.send_reminder_email(session_data)
                    if success:
                        sent_count += 1
                        logger.info(f"Sent reminder for session {session.id}")
                    else:
                        logger.warning(f"Failed to send reminder for session {session.id}")
                else:
                    logger.warning(f"No student email for session {session.id}")
                    
            except Exception as e:
                logger.error(f"Error sending reminder for session {session.id}: {e}")
        
        logger.info(f"Sent {sent_count} session reminders")
        return f"Sent {sent_count} reminders"
        
    except Exception as e:
        logger.error(f"Error in send_session_reminders task: {e}")
        raise


@shared_task
def cleanup_old_sessions():
    """
    Clean up old completed or cancelled sessions.
    This task should be run periodically (e.g., daily).
    """
    try:
        # Delete sessions older than 1 year that are completed or cancelled
        cutoff_date = timezone.now() - timedelta(days=365)
        
        old_sessions = FollowUpSession.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'cancelled']
        )
        
        count = old_sessions.count()
        old_sessions.delete()
        
        logger.info(f"Cleaned up {count} old sessions")
        return f"Cleaned up {count} old sessions"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_sessions task: {e}")
        raise


@shared_task
def sync_calendar_events():
    """
    Sync calendar events for sessions that have Google Calendar integration enabled.
    This task should be run periodically to ensure calendar events are up to date.
    """
    try:
        # Find sessions with Google Calendar integration that might need syncing
        sessions = FollowUpSession.objects.filter(
            add_to_google_calendar=True,
            status='scheduled',
            google_calendar_event_id__isnull=False
        ).select_related('student', 'teacher', 'subject', 'topic')
        
        synced_count = 0
        for session in sessions:
            try:
                # Prepare session data
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
                }
                
                # Update the calendar event
                success = google_calendar_service.update_event(
                    session.google_calendar_event_id, 
                    session_data
                )
                
                if success:
                    synced_count += 1
                    logger.info(f"Synced calendar event for session {session.id}")
                else:
                    logger.warning(f"Failed to sync calendar event for session {session.id}")
                    
            except Exception as e:
                logger.error(f"Error syncing calendar event for session {session.id}: {e}")
        
        logger.info(f"Synced {synced_count} calendar events")
        return f"Synced {synced_count} calendar events"
        
    except Exception as e:
        logger.error(f"Error in sync_calendar_events task: {e}")
        raise
