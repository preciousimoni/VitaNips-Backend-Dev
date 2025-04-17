from django.db import models
from django.conf import settings
from doctors.models import Prescription, PrescriptionItem

class Pharmacy(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    operating_hours = models.TextField()
    is_24_hours = models.BooleanField(default=False)
    offers_delivery = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    order_date = models.DateTimeField(auto_now_add=True)
    pickup_or_delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.user.email} - {self.status}"

class MedicationOrderItem(models.Model):
    order = models.ForeignKey(MedicationOrder, on_delete=models.CASCADE, related_name='items')
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.SET_NULL, null=True, blank=True)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Order {self.order.id} - {self.medication.name}"
    
    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

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
    custom_frequency = models.CharField(max_length=100, blank=True, null=True)  # For 'custom' frequency
    dosage = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.medication.name} - {self.time_of_day}"