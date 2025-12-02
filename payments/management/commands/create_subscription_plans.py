# payments/management/commands/create_subscription_plans.py
from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        # Free Plan - Only: basic reminders, health tracking
        free_plan, created = SubscriptionPlan.objects.get_or_create(
            tier='free',
            defaults={
                'name': 'Free',
                'description': 'Basic features for all users',
                'monthly_price': 0,
                'annual_price': 0,
                'features': {
                    'max_appointments_per_month': 3,
                    'health_tracking': True,
                    'basic_reminders': True,
                    'export_reports': False,
                    'priority_booking': False,
                    '24_7_support': False,
                    'advanced_analytics': False,
                    'medication_reminders': False,
                    'family_dashboard': False,
                    'shared_reminders': False,
                },
                'max_appointments_per_month': 3,
                'max_family_members': 1,
                'is_active': True
            }
        )
        # Update existing free plan if it exists
        if not created:
            free_plan.features = {
                'max_appointments_per_month': 3,
                'health_tracking': True,
                'basic_reminders': True,
                'export_reports': False,
                'priority_booking': False,
                '24_7_support': False,
                'advanced_analytics': False,
                'medication_reminders': False,
                'family_dashboard': False,
                'shared_reminders': False,
            }
            free_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Free plan features'))
        if created:
            self.stdout.write(self.style.SUCCESS('Created Free plan'))
        else:
            self.stdout.write(self.style.WARNING('Free plan already exists'))

        # Premium Plan - 24/7 support, export reports, health tracking, priority booking, 
        # advanced analytics, medication reminders, unlimited appointments
        # Pricing: ₦4,999/month (individual features would cost much more)
        premium_plan, created = SubscriptionPlan.objects.get_or_create(
            tier='premium',
            defaults={
                'name': 'Premium',
                'description': 'Unlimited appointments and advanced features',
                'monthly_price': 4999.00,  # ₦4,999/month
                'annual_price': 49990.00,  # ₦49,990/year (save ~17%)
                'features': {
                    'max_appointments_per_month': None,  # Unlimited
                    'health_tracking': True,
                    'advanced_analytics': True,
                    'export_reports': True,
                    'priority_booking': True,
                    '24_7_support': True,
                    'medication_reminders': True,
                    'basic_reminders': True,  # Premium includes basic reminders too
                    'family_dashboard': False,
                    'shared_reminders': False,
                },
                'max_appointments_per_month': None,
                'max_family_members': 1,
                'is_active': True
            }
        )
        # Update existing premium plan if it exists
        if not created:
            premium_plan.monthly_price = 4999.00
            premium_plan.annual_price = 49990.00
            premium_plan.features = {
                'max_appointments_per_month': None,  # Unlimited
                'health_tracking': True,
                'advanced_analytics': True,
                'export_reports': True,
                'priority_booking': True,
                '24_7_support': True,
                'medication_reminders': True,
                'basic_reminders': True,
                'family_dashboard': False,
                'shared_reminders': False,
            }
            premium_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Premium plan pricing and features'))
        if created:
            self.stdout.write(self.style.SUCCESS('Created Premium plan'))
        else:
            self.stdout.write(self.style.WARNING('Premium plan already exists'))

        # Family Plan - 24/7 support, export reports, health tracking, family dashboard,
        # priority booking, shared reminders, advanced analytics, unlimited appointments
        # Pricing: ₦8,999/month (for up to 5 family members)
        family_plan, created = SubscriptionPlan.objects.get_or_create(
            tier='family',
            defaults={
                'name': 'Family Plan',
                'description': 'Premium features for up to 5 family members',
                'monthly_price': 8999.00,  # ₦8,999/month
                'annual_price': 89990.00,  # ₦89,990/year (save ~17%)
                'features': {
                    'max_appointments_per_month': None,  # Unlimited
                    'health_tracking': True,
                    'advanced_analytics': True,
                    'export_reports': True,
                    'priority_booking': True,
                    '24_7_support': True,
                    'medication_reminders': True,
                    'basic_reminders': True,  # Family includes basic reminders too
                    'family_dashboard': True,
                    'shared_reminders': True,
                },
                'max_appointments_per_month': None,
                'max_family_members': 5,
                'is_active': True
            }
        )
        # Update existing family plan if it exists
        if not created:
            family_plan.monthly_price = 8999.00
            family_plan.annual_price = 89990.00
            family_plan.features = {
                'max_appointments_per_month': None,  # Unlimited
                'health_tracking': True,
                'advanced_analytics': True,
                'export_reports': True,
                'priority_booking': True,
                '24_7_support': True,
                'medication_reminders': True,
                'basic_reminders': True,
                'family_dashboard': True,
                'shared_reminders': True,
            }
            family_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Family plan pricing and features'))
        if created:
            self.stdout.write(self.style.SUCCESS('Created Family Plan'))
        else:
            self.stdout.write(self.style.WARNING('Family Plan already exists'))

        self.stdout.write(self.style.SUCCESS('Subscription plans setup complete!'))

