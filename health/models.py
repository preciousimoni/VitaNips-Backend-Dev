from django.db import models
from django.conf import settings

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
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='symptom_logs')
    symptom = models.CharField(max_length=200)
    date_experienced = models.DateTimeField()
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    duration = models.CharField(max_length=100, blank=True, null=True)  # e.g., "2 hours", "all day"
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
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='food_logs')
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