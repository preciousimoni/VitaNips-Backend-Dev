# users/management/commands/send_welcome_email.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from vitanips.core.utils import send_app_email
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Send welcome email to an existing user by email address or user ID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address of the user to send welcome email to',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID of the user to send welcome email to',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        user_id = options.get('user_id')
        
        if not email and not user_id:
            self.stdout.write(self.style.ERROR(
                '❌ Error: You must provide either --email or --user-id'
            ))
            return
        
        # Find user
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            identifier = email or f"ID {user_id}"
            self.stdout.write(self.style.ERROR(
                f'❌ User not found: {identifier}'
            ))
            return
        except User.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(
                f'❌ Multiple users found with email: {email}'
            ))
            return
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('Sending Welcome Email'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'User: {user.get_full_name() or user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'User ID: {user.id}')
        self.stdout.write('')
        
        # Prepare email context
        context = {
            'user': user,
            'subject': 'Welcome to VitaNips! 🎉'
        }
        
        self.stdout.write(f'Sending welcome email to {user.email}...')
        
        try:
            email_sent = send_app_email(
                to_email=user.email,
                subject=context['subject'],
                template_name='emails/welcome.html',
                context=context
            )
            
            if email_sent:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Welcome email sent successfully to {user.email}!'
                ))
                self.stdout.write('The user should receive the email shortly.')
                self.stdout.write('(Check spam folder if not in inbox)')
            else:
                self.stdout.write(self.style.ERROR(
                    '❌ Email sending returned False'
                ))
                self.stdout.write('Check the logs for error details.')
                self.stdout.write('')
                self.stdout.write('Common issues:')
                self.stdout.write('  1. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD')
                self.stdout.write('  2. For Zoho Mail, use an App Password (not regular password)')
                self.stdout.write('  3. Verify EMAIL_HOST and EMAIL_PORT are correct')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error sending email: {e}'))
            logger.error(f'Error sending welcome email to {user.email}: {e}', exc_info=True)

