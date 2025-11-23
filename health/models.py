# health/models.py
from django.db import models
from django.conf import settings
from doctors.models import Appointment


class VitalSign(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vital_signs')
    date_recorded = models.DateTimeField()

    # Common vital signs
    heart_rate = models.IntegerField(null=True, blank=True)  # BPM
    systolic_pressure = models.IntegerField(null=True, blank=True)  # mmHg
    diastolic_pressure = models.IntegerField(null=True, blank=True)  # mmHg
    respiratory_rate = models.IntegerField(null=True, blank=True)  # breaths per min
    temperature = models.FloatField(null=True, blank=True)  # Celsius
    oxygen_saturation = models.IntegerField(null=True, blank=True)  # %
    blood_glucose = models.FloatField(null=True, blank=True)  # mg/dL
    weight = models.FloatField(null=True, blank=True)  # kg

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.date_recorded}"


class SymptomLog(models.Model):
    SEVERITY_CHOICES = (
        (1, 'Mild'),
        (2, 'Moderate'),
        (3, 'Severe'),
        (4, 'Very Severe'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='symptom_logs')
    symptom = models.CharField(max_length=200)
    date_experienced = models.DateTimeField()
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    # e.g., "2 hours", "all day"
    duration = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.symptom} - {self.date_experienced}"


class FoodLog(models.Model):
    MEAL_CHOICES = (
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='food_logs')
    food_item = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES)
    datetime = models.DateTimeField()
    calories = models.IntegerField(null=True, blank=True)
    carbohydrates = models.FloatField(null=True, blank=True)  # grams
    proteins = models.FloatField(null=True, blank=True)  # grams
    fats = models.FloatField(null=True, blank=True)  # grams
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.food_item} - {self.datetime}"


class ExerciseLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exercise_logs')
    activity_type = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    duration = models.IntegerField()  # minutes
    calories_burned = models.IntegerField(null=True, blank=True)
    distance = models.FloatField(null=True, blank=True)  # kilometers
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.datetime}"


class SleepLog(models.Model):
    QUALITY_CHOICES = (
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Excellent'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sleep_logs')
    sleep_time = models.DateTimeField()
    wake_time = models.DateTimeField()
    quality = models.IntegerField(choices=QUALITY_CHOICES)
    interruptions = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.sleep_time.date()}"

    @property
    def duration(self):
        """Return sleep duration in hours"""
        delta = self.wake_time - self.sleep_time
        return delta.total_seconds() / 3600


class HealthGoal(models.Model):
    TYPE_CHOICES = (
        ('weight', 'Weight'),
        ('steps', 'Steps'),
        ('exercise', 'Exercise'),
        ('water', 'Water Intake'),
        ('sleep', 'Sleep'),
        ('custom', 'Custom'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='health_goals')
    goal_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    custom_type = models.CharField(max_length=100, blank=True, null=True)  # For 'custom' type
    target_value = models.FloatField()
    unit = models.CharField(max_length=50)  # e.g., "kg", "steps", "minutes"
    start_date = models.DateField()
    target_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    progress = models.FloatField(default=0.0)  # Percentage of completion
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.get_goal_type_display()} - {self.target_value} {self.unit}"


def user_directory_path(instance, filename):
    return f'user_{instance.uploaded_by.id}/documents/{filename}'


class MedicalDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medical_documents', help_text="The patient this document belongs to.")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents', help_text="User who uploaded the document (patient or doctor).")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    file = models.FileField(upload_to=user_directory_path, help_text="The actual uploaded file.")
    description = models.CharField( max_length=255, null=True, blank=True, help_text="Brief description or title of the document.")
    document_type = models.CharField(max_length=50, null=True, blank=True, help_text="e.g., Lab Result, Scan, Report, Prescription Image")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(null=True, blank=True, help_text="Size in bytes")
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_shared = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.file_size = self.file.size
            except:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        filename = 'Unknown File'
        if self.file:
            try:
                filename = self.file.name.split('/')[-1]
            except Exception:
                filename = str(self.file)
        return f"Document for {self.user.email} - {filename}"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Medical Document"
        verbose_name_plural = "Medical Documents"
