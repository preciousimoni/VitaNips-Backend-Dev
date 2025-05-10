# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True, unique=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    medical_history_summary = models.TextField(blank=True, null=True)
    
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    genotype = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)

    notify_appointment_confirmation_email = models.BooleanField(default=True)
    notify_appointment_cancellation_email = models.BooleanField(default=True)
    notify_appointment_reminder_email = models.BooleanField(default=True)
    notify_prescription_update_email = models.BooleanField(default=True)
    notify_order_update_email = models.BooleanField(default=True)
    notify_general_updates_email = models.BooleanField(default=True)
    notify_refill_reminder_email = models.BooleanField(default=True)

    notify_appointment_reminder_sms = models.BooleanField(default=False)

    notify_appointment_reminder_push = models.BooleanField(default=True)

    is_pharmacy_staff = models.BooleanField(_("pharmacy staff status"), default=False, help_text=_("Designates whether the user can log into the pharmacy portal."),)
    works_at_pharmacy = models.ForeignKey('pharmacy.Pharmacy', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members', help_text=_("The pharmacy this staff member belongs to."),)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class MedicalHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_history')
    condition = models.CharField(max_length=200)
    diagnosis_date = models.DateField()
    treatment = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.condition}"

class Vaccination(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=200)
    date_administered = models.DateField()
    dose_number = models.PositiveIntegerField(default=1)
    next_dose_date = models.DateField(null=True, blank=True)
    administered_at = models.CharField(max_length=200, blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.vaccine_name} (Dose {self.dose_number})"