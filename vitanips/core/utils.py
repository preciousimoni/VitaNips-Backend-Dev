# vitanips/core/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_app_email(to_email: str, subject: str, template_name: str, context: dict):
    """Helper function to send templated emails."""
    try:
        # Check email backend configuration
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        if 'console' in email_backend.lower():
            logger.warning(
                f"EMAIL_BACKEND is set to console - emails will not be sent. "
                f"Email would be sent to {to_email} with subject: {subject}"
            )
            # Still return True to not break registration flow
            return True
        
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL

        logger.info(f"Sending email to {to_email} using backend: {email_backend}")
        
        result = send_mail(
            subject,
            plain_message,
            from_email,
            [to_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"Email sent successfully to {to_email} with subject: {subject}")
            return True
        else:
            logger.warning(f"Email sending returned False for {to_email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
        return False