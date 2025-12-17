# users/management/commands/test_email.py
from django.core.management.base import BaseCommand
from django.conf import settings
from vitanips.core.utils import send_app_email


class Command(BaseCommand):
    help = 'Test email sending configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            required=True,
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('Testing Email Configuration'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        
        # Display current email configuration
        self.stdout.write('Current Email Configuration:')
        self.stdout.write(f"  EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        self.stdout.write(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"  EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        self.stdout.write(f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        self.stdout.write('')
        
        # Check if console backend
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        if 'console' in email_backend.lower():
            self.stdout.write(self.style.ERROR(
                '⚠️  WARNING: EMAIL_BACKEND is set to console. '
                'Emails will only be printed to console, not actually sent!'
            ))
            self.stdout.write('')
        
        # Send test email
        self.stdout.write(f'Sending test email to {test_email}...')
        self.stdout.write('')
        
        context = {
            'user': type('User', (), {'first_name': 'Test', 'email': test_email})(),
            'subject': 'VitaNips Email Test'
        }
        
        try:
            result = send_app_email(
                to_email=test_email,
                subject='VitaNips Email Configuration Test',
                template_name='emails/welcome.html',
                context=context
            )
            
            if result:
                self.stdout.write(self.style.SUCCESS('✅ Email sent successfully!'))
                self.stdout.write(f'Check your inbox at {test_email} (and spam folder)')
            else:
                self.stdout.write(self.style.ERROR('❌ Email sending returned False'))
                self.stdout.write('Check the logs above for error details')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error sending email: {e}'))
            self.stdout.write('')
            self.stdout.write('Common issues:')
            self.stdout.write('  1. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD')
            self.stdout.write('  2. For Zoho Mail, use an App Password (not regular password)')
            self.stdout.write('  3. Verify EMAIL_HOST and EMAIL_PORT are correct')
            self.stdout.write('  4. Check firewall/network restrictions')
            self.stdout.write('')
            self.stdout.write('For Zoho Mail setup:')
            self.stdout.write('  - Go to Zoho Mail → Settings → Security → App Passwords')
            self.stdout.write('  - Generate a new app password for "Mail Client"')
            self.stdout.write('  - Use that password in EMAIL_HOST_PASSWORD')

