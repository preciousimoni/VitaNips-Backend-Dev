# payments/management/commands/activate_pharmacy_subscription.py
from django.core.management.base import BaseCommand
from payments.models import PharmacySubscriptionRecord
from pharmacy.models import Pharmacy
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Activate pharmacy subscription by payment reference or pharmacy ID'

    def add_arguments(self, parser):
        parser.add_argument('--reference', type=str, help='Payment reference')
        parser.add_argument('--pharmacy-id', type=int, help='Pharmacy ID')
        parser.add_argument('--list-pending', action='store_true', help='List all pending subscriptions')

    def handle(self, *args, **options):
        if options['list_pending']:
            pending = PharmacySubscriptionRecord.objects.filter(status='pending')
            self.stdout.write(f"\nFound {pending.count()} pending subscriptions:\n")
            for sub in pending:
                self.stdout.write(
                    f"ID: {sub.id} | Pharmacy: {sub.pharmacy.name} | "
                    f"Reference: {sub.payment_reference or 'N/A'} | "
                    f"Created: {sub.created_at}"
                )
            return

        reference = options.get('reference')
        pharmacy_id = options.get('pharmacy_id')

        if reference:
            try:
                subscription = PharmacySubscriptionRecord.objects.get(payment_reference=reference)
                self.activate_subscription(subscription)
            except PharmacySubscriptionRecord.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No subscription found with reference: {reference}'))
        elif pharmacy_id:
            try:
                pharmacy = Pharmacy.objects.get(id=pharmacy_id)
                subscription = PharmacySubscriptionRecord.objects.filter(
                    pharmacy=pharmacy
                ).order_by('-created_at').first()
                
                if subscription:
                    self.activate_subscription(subscription)
                else:
                    self.stdout.write(self.style.ERROR(f'No subscription found for pharmacy: {pharmacy.name}'))
            except Pharmacy.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No pharmacy found with ID: {pharmacy_id}'))
        else:
            self.stdout.write(self.style.ERROR('Please provide --reference or --pharmacy-id or use --list-pending'))

    def activate_subscription(self, subscription):
        self.stdout.write(f"\nActivating subscription for: {subscription.pharmacy.name}")
        self.stdout.write(f"Plan: {subscription.plan.name}")
        self.stdout.write(f"Amount: ₦{subscription.amount}")
        
        subscription.status = 'active'
        subscription.save()
        
        # Update pharmacy expiry
        pharmacy = subscription.pharmacy
        pharmacy.subscription_expiry = subscription.current_period_end
        pharmacy.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSubscription activated successfully!'
            f'\nExpiry date: {pharmacy.subscription_expiry}'
        ))
