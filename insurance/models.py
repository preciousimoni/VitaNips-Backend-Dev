# insurance/models.py
from django.db import models
from django.conf import settings

class InsuranceProvider(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='insurance_logos/', null=True, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class InsurancePlan(models.Model):
    PLAN_TYPE_CHOICES = (
        ('HMO', 'Health Maintenance Organization'),
        ('PPO', 'Preferred Provider Organization'),
        ('EPO', 'Exclusive Provider Organization'),
        ('POS', 'Point of Service'),
        ('HDHP', 'High Deductible Health Plan'),
        ('other', 'Other'),
    )
    
    provider = models.ForeignKey(InsuranceProvider, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE_CHOICES)
    description = models.TextField()
    monthly_premium = models.DecimalField(max_digits=10, decimal_places=2)
    annual_deductible = models.DecimalField(max_digits=10, decimal_places=2)
    out_of_pocket_max = models.DecimalField(max_digits=10, decimal_places=2)
    coverage_details = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.provider.name} - {self.name}"

class UserInsurance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insurance_plans')
    plan = models.ForeignKey(InsurancePlan, on_delete=models.CASCADE, related_name='enrolled_users')
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True, null=True)
    member_id = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    insurance_card_front = models.ImageField(upload_to='insurance_cards/', null=True, blank=True)
    insurance_card_back = models.ImageField(upload_to='insurance_cards/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan}"

class InsuranceClaim(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('additional_info', 'Additional Information Needed'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('denied', 'Denied'),
        ('paid', 'Paid'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insurance_claims')
    user_insurance = models.ForeignKey(UserInsurance, on_delete=models.CASCADE, related_name='claims')
    claim_number = models.CharField(max_length=100)
    service_date = models.DateField()
    provider_name = models.CharField(max_length=200)
    service_description = models.TextField()
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    patient_responsibility = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    date_submitted = models.DateField()
    date_processed = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Claim {self.claim_number} - {self.user.email}"

class InsuranceDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insurance_documents')
    user_insurance = models.ForeignKey(UserInsurance, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    claim = models.ForeignKey(InsuranceClaim, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    title = models.CharField(max_length=200)
    document = models.FileField(upload_to='insurance_documents/')
    document_type = models.CharField(max_length=100)
    date_uploaded = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"