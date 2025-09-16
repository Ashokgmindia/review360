import random
from django.core.mail import send_mail
from django.conf import settings
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def send_otp_email(email, otp, subject, message_template):
    """Send an email with the OTP code."""
    message = message_template.format(otp=otp)
    from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        send_mail(subject, message, from_email, [email], fail_silently=False)
        logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        return False