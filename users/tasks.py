# users/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from vitanips.core.utils import send_app_email
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name="users.tasks.send_welcome_email")
def send_welcome_email(user_id: int):
    """Send welcome email to newly registered user."""
    try:
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'subject': 'Welcome to VitaNips! 🎉'
        }
        
        logger.info(f"Sending welcome email to user {user_id} ({user.email})")
        
        email_sent = send_app_email(
            to_email=user.email,
            subject=context['subject'],
            template_name='emails/welcome.html',
            context=context
        )
        
        if email_sent:
            logger.info(f"Welcome email sent successfully to {user.email}")
        else:
            logger.warning(f"Welcome email sending returned False for {user.email}")
            
        return email_sent
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for welcome email")
        return False
    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {e}", exc_info=True)
        return False

