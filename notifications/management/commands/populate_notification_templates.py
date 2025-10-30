from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Populate initial notification templates'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Appointment Reminder - 24 Hours',
                'template_type': 'appointment_reminder',
                'email_subject': 'Appointment Reminder: {{doctor_name}} - {{appointment_time}}',
                'email_body_html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2>Hello {{user.first_name}}!</h2>
                        <p>This is a friendly reminder about your upcoming appointment.</p>
                        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Doctor:</strong> {{doctor_name}}</p>
                            <p><strong>Date & Time:</strong> {{appointment_time}}</p>
                        </div>
                        <p>Please arrive 10 minutes early to complete any necessary paperwork.</p>
                        <p><a href="{{action_url}}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Appointment</a></p>
                    </body>
                    </html>
                ''',
                'email_body_text': 'Hello {{user.first_name}}! Reminder: Appointment with {{doctor_name}} at {{appointment_time}}',
                'sms_body': 'Reminder: Appointment with {{doctor_name}} tomorrow. {{appointment_time}}',
                'push_title': 'Appointment Reminder',
                'push_body': 'Tomorrow: {{doctor_name}} at {{appointment_time}}',
                'in_app_message': 'Your appointment with {{doctor_name}} is tomorrow at {{appointment_time}}',
            },
            {
                'name': 'Appointment Confirmation',
                'template_type': 'appointment_confirmation',
                'email_subject': 'Appointment Confirmed with {{doctor_name}}',
                'email_body_html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2>Appointment Confirmed!</h2>
                        <p>Your appointment has been successfully booked.</p>
                        <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Doctor:</strong> {{doctor_name}}</p>
                            <p><strong>Date & Time:</strong> {{appointment_time}}</p>
                            <p><strong>Type:</strong> {{appointment_type}}</p>
                        </div>
                        <p><a href="{{action_url}}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Details</a></p>
                    </body>
                    </html>
                ''',
                'email_body_text': 'Confirmed: Appointment with {{doctor_name}} on {{appointment_time}}',
                'sms_body': 'Confirmed: {{doctor_name}} on {{appointment_time}}',
                'push_title': 'Appointment Confirmed',
                'push_body': '{{doctor_name}} - {{appointment_time}}',
                'in_app_message': 'Your appointment with {{doctor_name}} is confirmed for {{appointment_time}}',
            },
            {
                'name': 'Medication Refill Reminder',
                'template_type': 'refill_reminder',
                'email_subject': 'Time to Refill: {{medication_name}}',
                'email_body_html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2>Medication Refill Reminder</h2>
                        <p>Your medication is running low and needs to be refilled soon.</p>
                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Medication:</strong> {{medication_name}}</p>
                            <p><strong>Days Remaining:</strong> {{days_remaining}}</p>
                        </div>
                        <p><a href="{{action_url}}" style="background-color: #ff9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Order Refill</a></p>
                    </body>
                    </html>
                ''',
                'email_body_text': 'Refill reminder: {{medication_name}} - {{days_remaining}} days remaining',
                'sms_body': 'Refill {{medication_name}} - {{days_remaining}} days left',
                'push_title': 'Medication Refill Needed',
                'push_body': '{{medication_name}} - {{days_remaining}} days remaining',
                'in_app_message': 'Time to refill {{medication_name}}. You have {{days_remaining}} days remaining.',
            },
            {
                'name': 'Prescription Ready',
                'template_type': 'prescription_ready',
                'email_subject': 'Your Prescription is Ready for Pickup',
                'email_body_html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2>Prescription Ready!</h2>
                        <p>Your prescription is now ready for pickup at your chosen pharmacy.</p>
                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Pharmacy:</strong> {{pharmacy_name}}</p>
                            <p><strong>Address:</strong> {{pharmacy_address}}</p>
                            <p><strong>Order Number:</strong> {{order_number}}</p>
                        </div>
                        <p>Please bring a valid ID when picking up your prescription.</p>
                    </body>
                    </html>
                ''',
                'email_body_text': 'Your prescription is ready at {{pharmacy_name}}. Order #{{order_number}}',
                'sms_body': 'Prescription ready at {{pharmacy_name}}',
                'push_title': 'Prescription Ready',
                'push_body': 'Ready for pickup at {{pharmacy_name}}',
                'in_app_message': 'Your prescription is ready for pickup at {{pharmacy_name}}',
            },
            {
                'name': 'Test Results Available',
                'template_type': 'test_results',
                'email_subject': 'Your Test Results are Available',
                'email_body_html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2>Test Results Available</h2>
                        <p>Your recent test results have been uploaded and are now available for review.</p>
                        <p><a href="{{action_url}}" style="background-color: #673ab7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Results</a></p>
                        <p style="color: #666; font-size: 12px;">Please consult with your doctor to discuss these results.</p>
                    </body>
                    </html>
                ''',
                'email_body_text': 'Your test results are available. Log in to view them.',
                'sms_body': 'Your test results are now available',
                'push_title': 'Test Results Available',
                'push_body': 'Tap to view your recent test results',
                'in_app_message': 'Your test results are now available for review',
            },
            {
                'name': 'Emergency Alert',
                'template_type': 'emergency_alert',
                'email_subject': 'URGENT: Emergency Alert from {{user.first_name}}',
                'email_body_html': '''
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        <h2 style="color: red;">⚠️ EMERGENCY ALERT</h2>
                        <p><strong>{{user.first_name}} {{user.last_name}}</strong> has triggered an emergency alert.</p>
                        <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid red;">
                            <p><strong>Time:</strong> {{alert_time}}</p>
                            <p><strong>Location:</strong> {{location}}</p>
                        </div>
                        <p style="color: red; font-weight: bold;">Please respond immediately.</p>
                    </body>
                    </html>
                ''',
                'email_body_text': 'EMERGENCY: {{user.first_name}} needs immediate assistance at {{location}}',
                'sms_body': 'EMERGENCY ALERT from {{user.first_name}} at {{location}}',
                'push_title': '⚠️ EMERGENCY ALERT',
                'push_body': '{{user.first_name}} needs immediate assistance',
                'in_app_message': 'Emergency alert triggered by {{user.first_name}}',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {template.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Updated: {template.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully processed {len(templates)} templates'))
        self.stdout.write(self.style.SUCCESS(f'   Created: {created_count}, Updated: {updated_count}'))
