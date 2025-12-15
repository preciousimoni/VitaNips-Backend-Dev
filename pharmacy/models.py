# pharmacy/models.py
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from doctors.models import Prescription, PrescriptionItem
import requests
import logging

logger = logging.getLogger(__name__)

class Pharmacy(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    location = gis_models.PointField(null=True, blank=True, srid=4326)
    operating_hours = models.TextField()
    is_24_hours = models.BooleanField(default=False)
    offers_delivery = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Is the pharmacy currently operational and accepting orders?")
    
    # Payment & Subscription Fields
    subaccount_id = models.CharField(max_length=100, blank=True, null=True, help_text="Flutterwave Subaccount ID for split payments")
    bank_account_details = models.JSONField(default=dict, blank=True, help_text="Bank account details")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Platform commission percentage for this pharmacy")
    subscription_expiry = models.DateField(null=True, blank=True, help_text="Date when the pharmacy's registration expires")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatic Geocoding if location is missing but address is present
        if not self.location and self.address:
            try:
                api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
                if api_key:
                    response = requests.get(
                        'https://maps.googleapis.com/maps/api/geocode/json',
                        params={'address': self.address, 'key': api_key}
                    )
                    data = response.json()
                    
                    if data.get('status') == 'OK' and data.get('results'):
                        location = data['results'][0]['geometry']['location']
                        lat = location['lat']
                        lng = location['lng']
                        # Point takes (x, y) which is (longitude, latitude)
                        self.location = Point(lng, lat, srid=4326)
                    else:
                        logger.warning(f"Geocoding failed for pharmacy {self.name}: {data.get('status')}")
                else:
                    logger.warning("GOOGLE_MAPS_API_KEY not found in settings. Automatic geocoding skipped.")
            except Exception as e:
                logger.error(f"Error during automatic geocoding for pharmacy {self.name}: {e}")

        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Pharmacies"

class Medication(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    dosage_form = models.CharField(max_length=100)  # e.g., tablet, capsule, liquid
    strength = models.CharField(max_length=100)     # e.g., 500mg, 250ml
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    requires_prescription = models.BooleanField(default=True)
    side_effects = models.TextField(blank=True, null=True)
    contraindications = models.TextField(blank=True, null=True)
    storage_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} {self.strength} {self.dosage_form}"

class PharmacyInventory(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='inventory')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='inventories')
    in_stock = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.pharmacy.name} - {self.medication.name} - {'In Stock' if self.in_stock else 'Out of Stock'}"
    
    class Meta:
        verbose_name_plural = "Pharmacy Inventories"
        unique_together = ('pharmacy', 'medication')

class MedicationOrder(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready for Pickup'),
        ('delivering', 'Out for Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medication_orders')
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='orders')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_delivery = models.BooleanField(default=False)
    delivery_address = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Insurance fields
    user_insurance = models.ForeignKey('insurance.UserInsurance', on_delete=models.SET_NULL, null=True, blank=True, related_name='medication_orders', help_text="Insurance plan used for this order")
    insurance_covered_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Amount covered by insurance")
    patient_copay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Patient's out-of-pocket amount")
    insurance_claim_generated = models.BooleanField(default=False, help_text="Whether an insurance claim was automatically generated")
    
    # Payment fields
    payment_reference = models.CharField(max_length=255, null=True, blank=True, help_text="Payment reference/transaction ID from payment gateway")
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending',
        help_text="Payment status for the order"
    )
    
    order_date = models.DateTimeField(auto_now_add=True)
    pickup_or_delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.status}"

class MedicationOrderItem(models.Model):
    order = models.ForeignKey(MedicationOrder, on_delete=models.CASCADE, related_name='items')
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.SET_NULL, null=True, blank=True)
    medication_name_text = models.CharField(max_length=200, null=True, blank=True, help_text="Medication name as written on prescription")
    dosage_text = models.CharField(max_length=100, null=True, blank=True, help_text="Dosage as written on prescription")
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.order.id} - {self.medication_name_text}"
    
    @property
    def total_price(self):
        if self.quantity and self.price_per_unit:
             return self.quantity * self.price_per_unit
        return None

class MedicationReminder(models.Model):
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medication_reminders')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='reminders')
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    time_of_day = models.TimeField()
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    custom_frequency = models.CharField(max_length=100, blank=True, null=True)
    dosage = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class MedicationLog(models.Model):
    STATUS_CHOICES = (
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
    )

    reminder = models.ForeignKey(MedicationReminder, on_delete=models.CASCADE, related_name='logs')
    scheduled_time = models.DateTimeField()
    taken_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='taken')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reminder.medication.name} - {self.status} at {self.taken_at or self.scheduled_time}"

    class Meta:
        ordering = ['-scheduled_time']