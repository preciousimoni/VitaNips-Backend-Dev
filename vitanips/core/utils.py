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
        email_host = getattr(settings, 'EMAIL_HOST', '')
        email_host_user = getattr(settings, 'EMAIL_HOST_USER', '')
        
        logger.info(f"Email configuration - Backend: {email_backend}, Host: {email_host}, User: {email_host_user}")
        
        if 'console' in email_backend.lower():
            logger.warning(
                f"EMAIL_BACKEND is set to console - emails will not be sent. "
                f"Email would be sent to {to_email} with subject: {subject}"
            )
            # Still return True to not break registration flow
            return True
        
        # Verify email settings are configured
        if not email_host or not email_host_user:
            logger.error(f"Email settings not fully configured. EMAIL_HOST: {email_host}, EMAIL_HOST_USER: {email_host_user}")
            return False
        
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL

        logger.info(f"Attempting to send email to {to_email} using backend: {email_backend}")
        logger.debug(f"From: {from_email}, Subject: {subject}")
        
        result = send_mail(
            subject,
            plain_message,
            from_email,
            [to_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"✅ Email sent successfully to {to_email} with subject: {subject}")
            return True
        else:
            logger.warning(f"⚠️ Email sending returned False for {to_email}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Provide specific error messages for common issues
        if 'authentication failed' in error_msg.lower() or '535' in error_msg:
            logger.error(
                f"❌ SMTP Authentication failed for {to_email}. "
                f"Error: {error_msg}\n"
                f"🔧 TROUBLESHOOTING:\n"
                f"   1. For Zoho Mail: You MUST use an App Password, not your regular password.\n"
                f"      - Go to Zoho Mail → Settings → Security → App Passwords\n"
                f"      - Generate a new app password for 'Mail Client'\n"
                f"      - Use this app password in EMAIL_HOST_PASSWORD\n"
                f"   2. Verify EMAIL_HOST_USER is correct: {email_host_user}\n"
                f"   3. Ensure 2FA is enabled (required for app passwords)\n"
                f"   4. Check that the password doesn't have extra spaces or quotes"
            )
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            logger.error(
                f"❌ SMTP Connection error for {to_email}. "
                f"Check EMAIL_HOST and EMAIL_PORT. "
                f"Error: {error_msg}"
            )
        else:
            logger.error(
                f"❌ Error sending email to {to_email}: {error_type} - {error_msg}",
                exc_info=True
            )
        return False