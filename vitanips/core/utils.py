# vitanips/core/utils.py (create core app or place appropriately)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

def send_app_email(to_email: str, subject: str, template_name: str, context: dict):
    """Helper function to send templated emails."""
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message) # Generate plain text version
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject,
            plain_message,
            from_email,
            [to_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Email sent successfully to {to_email} with subject: {subject}") # For logging
        return True
    except Exception as e:
        # Log the error properly in production
        print(f"Error sending email to {to_email}: {e}")
        return False