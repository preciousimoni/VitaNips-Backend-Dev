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
    
    # Coverage Percentages
    consultation_coverage_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=90.00,
        help_text="Percentage of consultation fees covered (0-100)"
    )
    medication_coverage_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=85.00,
        help_text="Percentage of medication costs covered (0-100)"
    )
    lab_test_coverage_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=80.00,
        help_text="Percentage of lab test costs covered (0-100)"
    )
    
    # Annual Limits
    max_consultations_per_year = models.IntegerField(
        null=True, blank=True,
        help_text="Maximum number of consultations covered per year (null = unlimited)"
    )
    max_medication_amount_per_year = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Maximum medication cost covered per year in Naira (null = unlimited)"
    )
    max_lab_tests_per_year = models.IntegerField(
        null=True, blank=True,
        help_text="Maximum number of lab tests covered per year (null = unlimited)"
    )
    
    # Service Coverage Flags
    covers_telemedicine = models.BooleanField(default=True, help_text="Covers virtual consultations")
    covers_emergency = models.BooleanField(default=True, help_text="Covers emergency services")
    covers_maternity = models.BooleanField(default=False, help_text="Covers maternity care")
    covers_dental = models.BooleanField(default=False, help_text="Covers dental services")
    covers_optical = models.BooleanField(default=False, help_text="Covers optical/vision services")
    covers_lab_tests = models.BooleanField(default=True, help_text="Covers laboratory tests")
    covers_surgery = models.BooleanField(default=False, help_text="Covers surgical procedures")
    covers_physiotherapy = models.BooleanField(default=False, help_text="Covers physiotherapy")
    
    # Pre-authorization Requirements
    requires_preauth_for_specialist = models.BooleanField(
        default=False,
        help_text="Requires pre-authorization for specialist consultations"
    )
    requires_preauth_for_surgery = models.BooleanField(
        default=True,
        help_text="Requires pre-authorization for surgical procedures"
    )
    preauth_threshold_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Amount above which pre-authorization is required (in Naira)"
    )
    
    # Network Restrictions (JSON fields for flexibility)
    network_hospitals = models.JSONField(
        default=list, blank=True,
        help_text="List of approved hospital names/IDs"
    )
    network_pharmacies = models.JSONField(
        default=list, blank=True,
        help_text="List of approved pharmacy names/IDs"
    )
    network_labs = models.JSONField(
        default=list, blank=True,
        help_text="List of approved laboratory names/IDs"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.provider.name} - {self.name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Insurance Plan"
        verbose_name_plural = "Insurance Plans"

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


class HMOPayment(models.Model):
    """Track payments from HMO providers to the platform"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('disputed', 'Disputed'),
    )
    
    claim = models.OneToOneField(
        InsuranceClaim, on_delete=models.CASCADE, related_name='hmo_payment'
    )
    hmo_provider = models.ForeignKey(
        InsuranceProvider, on_delete=models.CASCADE, related_name='payments'
    )
    
    # Payment Breakdown
    service_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Original service cost"
    )
    hmo_covered_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Amount HMO is responsible for"
    )
    platform_processing_fee = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Platform's processing fee (percentage of covered amount)"
    )
    total_due_from_hmo = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Total amount HMO owes (covered + processing fee)"
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Amount actually paid by HMO"
    )
    
    # Payment Tracking
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending'
    )
    expected_payment_date = models.DateField(null=True, blank=True)
    date_paid = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=200, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"HMO Payment for Claim {self.claim.claim_number}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "HMO Payment"
        verbose_name_plural = "HMO Payments"


class HMOInvoice(models.Model):
    """Monthly invoices sent to HMO providers"""
    INVOICE_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
    )
    
    hmo_provider = models.ForeignKey(
        InsuranceProvider, on_delete=models.CASCADE, related_name='invoices'
    )
    invoice_number = models.CharField(max_length=100, unique=True)
    
    # Period
    month = models.IntegerField(help_text="Month (1-12)")
    year = models.IntegerField(help_text="Year")
    
    # Totals
    total_claims = models.IntegerField(default=0)
    total_covered_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    platform_processing_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='draft')
    date_sent = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    date_paid = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.hmo_provider.name}"
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['hmo_provider', 'month', 'year']
        verbose_name = "HMO Invoice"
        verbose_name_plural = "HMO Invoices"


class PreAuthorization(models.Model):
    """Pre-authorization requests for high-cost services"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('expired', 'Expired'),
    )
    
    SERVICE_TYPE_CHOICES = (
        ('specialist', 'Specialist Consultation'),
        ('surgery', 'Surgical Procedure'),
        ('expensive_medication', 'Expensive Medication'),
        ('lab_test', 'Laboratory Test'),
        ('imaging', 'Imaging/Radiology'),
        ('other', 'Other'),
    )
    
    user_insurance = models.ForeignKey(
        UserInsurance, on_delete=models.CASCADE, related_name='preauthorizations'
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    service_description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(help_text="Medical justification for the service")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hmo_reference_number = models.CharField(max_length=200, blank=True, null=True)
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(
        null=True, blank=True,
        help_text="Date when pre-authorization expires"
    )
    
    # Response
    hmo_response = models.TextField(blank=True, null=True)
    approved_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Amount approved by HMO (may differ from estimated cost)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PreAuth {self.id} - {self.user_insurance.user.email} - {self.service_type}"
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = "Pre-Authorization"
        verbose_name_plural = "Pre-Authorizations"