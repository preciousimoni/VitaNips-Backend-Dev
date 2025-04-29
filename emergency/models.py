# emergency/models.py
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models  # Import GeoDjango models

class EmergencyService(models.Model):
    TYPE_CHOICES = (
        ('hospital', 'Hospital'),
        ('ambulance', 'Ambulance Service'),
        ('fire', 'Fire Department'),
        ('police', 'Police Station'),
        ('poison', 'Poison Control'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=200)
    service_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = gis_models.PointField(null=True, blank=True, srid=4326)  # GeoDjango PointField
    is_24_hours = models.BooleanField(default=True)
    operating_hours = models.TextField(blank=True, null=True)
    has_emergency_room = models.BooleanField(default=False)
    provides_ambulance = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"
    
    class Meta:
        verbose_name_plural = "Emergency Services"

class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = (
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('relative', 'Other Relative'),
        ('friend', 'Friend'),
        ('doctor', 'Doctor'),
        ('caregiver', 'Caregiver'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    phone_number = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()}) - Contact for {self.user.email}"

class EmergencyAlert(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('responded', 'Responded'),
        ('resolved', 'Resolved'),
        ('false_alarm', 'False Alarm'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emergency_alerts')
    initiated_at = models.DateTimeField(auto_now_add=True)
    location = gis_models.PointField(null=True, blank=True, srid=4326)  # GeoDjango PointField
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Emergency Alert - {self.user.email} - {self.initiated_at}"

class EmergencyAlertContact(models.Model):
    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, related_name='contacted_persons')
    contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE, related_name='received_alerts')
    sent_at = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=50, default='pending')
    response_received = models.BooleanField(default=False)
    response_time = models.DateTimeField(null=True, blank=True)
    response_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Alert to {self.contact.name} for {self.alert.user.email}"