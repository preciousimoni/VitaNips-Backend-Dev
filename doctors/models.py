# doctors/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
# from pharmacy.models import Medication

class Specialty(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Specialties"

class Doctor(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    APPLICATION_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialties = models.ManyToManyField(Specialty, related_name='doctors')
    profile_picture = models.ImageField(upload_to='doctor_pics/', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    years_of_experience = models.PositiveIntegerField(default=0)
    education = models.TextField()
    bio = models.TextField()
    languages_spoken = models.CharField(max_length=200)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available_for_virtual = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Application fields
    application_status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default='draft',
        help_text="Status of the doctor's application"
    )
    license_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Medical license number"
    )
    license_issuing_authority = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Authority that issued the license"
    )
    license_expiry_date = models.DateField(
        blank=True,
        null=True,
        help_text="License expiration date"
    )
    hospital_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of the hospital/clinic where the doctor works"
    )
    hospital_address = models.TextField(
        blank=True,
        null=True,
        help_text="Address of the hospital/clinic"
    )
    hospital_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Hospital/clinic contact phone number"
    )
    hospital_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Hospital/clinic contact email"
    )
    hospital_contact_person = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of contact person at hospital"
    )
    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the application was submitted for review"
    )
    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the application was last reviewed"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_doctors',
        help_text="Admin who reviewed the application"
    )
    review_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Admin review notes and comments"
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection if application was rejected"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"
    
    @property
    def average_rating(self):
        ratings = self.reviews.all()
        if ratings:
            return sum(r.rating for r in ratings) / len(ratings)
        return 0

class DoctorReview(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # 1-5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.doctor.full_name} - {self.rating}"
    
    class Meta:
        unique_together = ('doctor', 'user')

class DoctorAvailability(models.Model):
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"
    
    class Meta:
        verbose_name_plural = "Doctor Availabilities"

class Appointment(models.Model):
    class StatusChoices(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'
        NO_SHOW = 'no_show', 'No Show'
    
    class TypeChoices(models.TextChoices):
        IN_PERSON = 'in_person', 'In-Person'
        VIRTUAL = 'virtual', 'Virtual'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(max_length=10, choices=TypeChoices.choices, default=TypeChoices.IN_PERSON)
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.SCHEDULED)
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    followup_required = models.BooleanField(default=False)
    
    # Insurance fields
    user_insurance = models.ForeignKey('insurance.UserInsurance', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments', help_text="Insurance plan used for this appointment")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total consultation fee")
    insurance_covered_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Amount covered by insurance")
    patient_copay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Patient's out-of-pocket amount")
    insurance_claim_generated = models.BooleanField(default=False, help_text="Whether an insurance claim was automatically generated")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.doctor.full_name} - {self.date} {self.start_time}"


class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    date_prescribed = models.DateField(auto_now_add=True)
    diagnosis = models.TextField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Prescription for {self.user.email} by {self.doctor.full_name}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey('pharmacy.Medication', on_delete=models.SET_NULL, null=True, blank=True, help_text="Link to the structured medication entry if available.")
    medication_name = models.CharField(max_length=200, help_text="Medication name as written, or if no structured entry linked.")
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField()
    
    def __str__(self):
        return f"{self.medication_name} ({self.medication.name if self.medication else 'N/A'}) - {self.dosage}"

class VirtualSession(models.Model):
    """Manages virtual consultation sessions via Twilio Video"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='virtual_session'
    )
    room_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique Twilio room identifier"
    )
    room_sid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twilio Room SID after creation"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Actual session duration"
    )
    recording_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to session recording if enabled"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Virtual Session for Appointment #{self.appointment.id} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.room_name:
            # Generate unique room name
            self.room_name = f"vitanips-{self.appointment.id}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Virtual Session"
        verbose_name_plural = "Virtual Sessions"
