"""
Google Calendar integration service for follow-up sessions.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    # Handle case where Google libraries are not installed
    GOOGLE_LIBS_AVAILABLE = False
    Credentials = None

logger = logging.getLogger(__name__)

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    """Service class for Google Calendar integration."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def _get_credentials(self):
        """Get or refresh Google Calendar credentials."""
        if not GOOGLE_LIBS_AVAILABLE:
            logger.error("Google Calendar libraries not available")
            return None
            
        try:
            # Try to load existing credentials
            creds = Credentials.from_authorized_user_file(
                settings.GOOGLE_CREDENTIALS_FILE, SCOPES
            )
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Check if we have web or installed app credentials
                    import json
                    with open(settings.GOOGLE_CLIENT_SECRETS_FILE, 'r') as f:
                        client_config = json.load(f)
                    
                    if 'web' in client_config:
                        # For web applications, we need to use a different flow
                        from google_auth_oauthlib.flow import Flow
                        flow = Flow.from_client_config(client_config, SCOPES)
                        flow.redirect_uri = 'http://localhost:8080/'
                        # For web apps, you'll need to handle the authorization URL manually
                        # This is a simplified version - in production, you'd want a proper web flow
                        creds = None
                        logger.warning("Web application credentials detected. Manual authorization required.")
                    else:
                        # For installed applications
                        flow = InstalledAppFlow.from_client_secrets_file(
                            settings.GOOGLE_CLIENT_SECRETS_FILE, SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                if creds:
                    with open(settings.GOOGLE_CREDENTIALS_FILE, 'w') as token:
                        token.write(creds.to_json())
            
            return creds
        except Exception as e:
            logger.error(f"Error getting Google Calendar credentials: {e}")
            return None
    
    def _get_service(self):
        """Get Google Calendar service instance."""
        if not GOOGLE_LIBS_AVAILABLE:
            logger.error("Google Calendar libraries not available")
            return None
            
        if not self.service:
            creds = self._get_credentials()
            if creds:
                self.service = build('calendar', 'v3', credentials=creds)
        return self.service
    
    def create_event(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a Google Calendar event for a follow-up session.
        
        Args:
            session_data: Dictionary containing session information
            
        Returns:
            Event ID if successful, None otherwise
        """
        if not GOOGLE_LIBS_AVAILABLE:
            logger.error("Google Calendar libraries not available")
            return None
            
        try:
            service = self._get_service()
            if not service:
                logger.error("Google Calendar service not available")
                return None
            
            # Prepare event data
            event = {
                'summary': f"Follow-up Session: {session_data.get('student_name', 'Student')}",
                'description': self._format_event_description(session_data),
                'start': {
                    'dateTime': session_data['session_datetime'].isoformat(),
                    'timeZone': str(timezone.get_current_timezone()),
                },
                'end': {
                    'dateTime': (session_data['session_datetime'] + timedelta(hours=1)).isoformat(),
                    'timeZone': str(timezone.get_current_timezone()),
                },
                'location': session_data.get('location', ''),
                'attendees': self._get_attendees(session_data),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours
                        {'method': 'popup', 'minutes': 30},       # 30 minutes
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': True,
            }
            
            # Create the event
            event_result = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if session_data.get('send_invitations', False) else 'none'
            ).execute()
            
            logger.info(f"Created Google Calendar event: {event_result.get('id')}")
            return event_result.get('id')
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            return None
    
    def update_event(self, event_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Update an existing Google Calendar event.
        
        Args:
            event_id: Google Calendar event ID
            session_data: Updated session information
            
        Returns:
            True if successful, False otherwise
        """
        if not GOOGLE_LIBS_AVAILABLE:
            logger.error("Google Calendar libraries not available")
            return False
            
        try:
            service = self._get_service()
            if not service:
                return False
            
            # Get existing event
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update event data
            event['summary'] = f"Follow-up Session: {session_data.get('student_name', 'Student')}"
            event['description'] = self._format_event_description(session_data)
            event['start'] = {
                'dateTime': session_data['session_datetime'].isoformat(),
                'timeZone': str(timezone.get_current_timezone()),
            }
            event['end'] = {
                'dateTime': (session_data['session_datetime'] + timedelta(hours=1)).isoformat(),
                'timeZone': str(timezone.get_current_timezone()),
            }
            event['location'] = session_data.get('location', '')
            event['attendees'] = self._get_attendees(session_data)
            
            # Update the event
            service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all' if session_data.get('send_invitations', False) else 'none'
            ).execute()
            
            logger.info(f"Updated Google Calendar event: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Calendar API error updating event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a Google Calendar event.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        if not GOOGLE_LIBS_AVAILABLE:
            logger.error("Google Calendar libraries not available")
            return False
            
        try:
            service = self._get_service()
            if not service:
                return False
            
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Calendar API error deleting event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            return False
    
    def _format_event_description(self, session_data: Dict[str, Any]) -> str:
        """Format event description with session details."""
        description_parts = []
        
        if session_data.get('objective'):
            description_parts.append(f"Objective: {session_data['objective']}")
        
        if session_data.get('notes_for_student'):
            description_parts.append(f"Notes for Student: {session_data['notes_for_student']}")
        
        if session_data.get('topic_name'):
            description_parts.append(f"Topic: {session_data['topic_name']}")
        
        if session_data.get('subject_name'):
            description_parts.append(f"Subject: {session_data['subject_name']}")
        
        return "\n\n".join(description_parts) if description_parts else "Follow-up session"
    
    def _get_attendees(self, session_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get attendees list for the calendar event."""
        attendees = []
        
        # Add student email if available
        if session_data.get('student_email'):
            attendees.append({
                'email': session_data['student_email'],
                'displayName': session_data.get('student_name', 'Student'),
                'responseStatus': 'needsAction'
            })
        
        # Add teacher email if available
        if session_data.get('teacher_email'):
            attendees.append({
                'email': session_data['teacher_email'],
                'displayName': session_data.get('teacher_name', 'Teacher'),
                'responseStatus': 'needsAction'
            })
        
        return attendees
    
    def send_email_invitation(self, session_data: Dict[str, Any], event_id: str = None) -> bool:
        """
        Send email invitation for the session.
        
        Args:
            session_data: Session information
            event_id: Google Calendar event ID (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            student_email = session_data.get('student_email')
            if not student_email:
                logger.warning("No student email provided for invitation")
                return False
            
            # Prepare email content
            subject = f"Follow-up Session Scheduled - {session_data.get('topic_name', 'Session')}"
            
            context = {
                'student_name': session_data.get('student_name', 'Student'),
                'teacher_name': session_data.get('teacher_name', 'Teacher'),
                'session_datetime': session_data['session_datetime'],
                'location': session_data.get('location', 'TBD'),
                'objective': session_data.get('objective', ''),
                'notes_for_student': session_data.get('notes_for_student', ''),
                'topic_name': session_data.get('topic_name', ''),
                'subject_name': session_data.get('subject_name', ''),
                'event_id': event_id,
            }
            
            # Render email template
            html_message = render_to_string('followup/email/session_invitation.html', context)
            plain_message = render_to_string('followup/email/session_invitation.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Sent email invitation to {student_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email invitation: {e}")
            return False
    
    def send_reminder_email(self, session_data: Dict[str, Any]) -> bool:
        """
        Send reminder email for an upcoming session.
        
        Args:
            session_data: Session information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            student_email = session_data.get('student_email')
            if not student_email:
                logger.warning("No student email provided for reminder")
                return False
            
            # Prepare email content
            subject = f"Reminder: Follow-up Session Tomorrow - {session_data.get('topic_name', 'Session')}"
            
            context = {
                'student_name': session_data.get('student_name', 'Student'),
                'teacher_name': session_data.get('teacher_name', 'Teacher'),
                'session_datetime': session_data['session_datetime'],
                'location': session_data.get('location', 'TBD'),
                'objective': session_data.get('objective', ''),
                'notes_for_student': session_data.get('notes_for_student', ''),
                'topic_name': session_data.get('topic_name', ''),
                'subject_name': session_data.get('subject_name', ''),
                'is_reminder': True,
            }
            
            # Render email template
            html_message = render_to_string('followup/email/session_reminder.html', context)
            plain_message = render_to_string('followup/email/session_reminder.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Sent reminder email to {student_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending reminder email: {e}")
            return False


# Global service instance
google_calendar_service = GoogleCalendarService()
