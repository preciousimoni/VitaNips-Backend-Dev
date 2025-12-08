from django.contrib import admin
from .models import (
    InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, 
    InsuranceDocument, HMOPayment, HMOInvoice, PreAuthorization
)

@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_phone', 'contact_email', 'website', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'contact_phone', 'contact_email', 'website')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'logo')
        }),
        ('Contact Information', {
            'fields': ('contact_phone', 'contact_email', 'website')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'plan_type', 'monthly_premium', 'consultation_coverage_percentage', 'is_active', 'created_at')
    search_fields = ('name', 'provider__name', 'description', 'coverage_details')
    list_filter = ('plan_type', 'is_active', 'covers_maternity', 'covers_dental', 'covers_optical', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Plan Information', {
            'fields': ('provider', 'name', 'plan_type', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('monthly_premium', 'annual_deductible', 'out_of_pocket_max')
        }),
        ('Coverage Percentages', {
            'fields': ('consultation_coverage_percentage', 'medication_coverage_percentage', 'lab_test_coverage_percentage')
        }),
        ('Annual Limits', {
            'fields': ('max_consultations_per_year', 'max_medication_amount_per_year', 'max_lab_tests_per_year'),
            'classes': ('collapse',)
        }),
        ('Service Coverage', {
            'fields': ('covers_telemedicine', 'covers_emergency', 'covers_maternity', 'covers_dental', 
                      'covers_optical', 'covers_lab_tests', 'covers_surgery', 'covers_physiotherapy')
        }),
        ('Pre-Authorization', {
            'fields': ('requires_preauth_for_specialist', 'requires_preauth_for_surgery', 'preauth_threshold_amount'),
            'classes': ('collapse',)
        }),
        ('Network Restrictions', {
            'fields': ('network_hospitals', 'network_pharmacies', 'network_labs'),
            'classes': ('collapse',)
        }),
        ('Coverage Details', {
            'fields': ('coverage_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserInsurance)
class UserInsuranceAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'policy_number', 'member_id', 'start_date', 'end_date', 'is_primary', 'created_at')
    search_fields = ('user__email', 'plan__name', 'policy_number', 'group_number', 'member_id')
    list_filter = ('is_primary', 'start_date', 'end_date', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'is_primary')
        }),
        ('Policy Information', {
            'fields': ('policy_number', 'group_number', 'member_id')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Insurance Cards', {
            'fields': ('insurance_card_front', 'insurance_card_back'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_number', 'user', 'user_insurance', 'service_date', 'status', 'claimed_amount', 'approved_amount', 'patient_responsibility', 'date_submitted')
    search_fields = ('user__email', 'claim_number', 'provider_name', 'service_description', 'notes')
    list_filter = ('status', 'service_date', 'date_submitted', 'date_processed', 'created_at')
    ordering = ('-date_submitted',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Claim Information', {
            'fields': ('user', 'user_insurance', 'claim_number', 'status')
        }),
        ('Service Details', {
            'fields': ('service_date', 'provider_name', 'service_description')
        }),
        ('Financial Information', {
            'fields': ('claimed_amount', 'approved_amount', 'patient_responsibility')
        }),
        ('Processing', {
            'fields': ('date_submitted', 'date_processed', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InsuranceDocument)
class InsuranceDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'user_insurance', 'claim', 'document_type', 'date_uploaded', 'created_at')
    search_fields = ('user__email', 'title', 'notes')
    list_filter = ('document_type', 'date_uploaded', 'created_at')
    ordering = ('-date_uploaded',)
    readonly_fields = ('created_at', 'date_uploaded')
    fieldsets = (
        ('Document Information', {
            'fields': ('user', 'user_insurance', 'claim', 'title', 'document_type', 'document', 'notes')
        }),
        ('Timestamps', {
            'fields': ('date_uploaded', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HMOPayment)
class HMOPaymentAdmin(admin.ModelAdmin):
    list_display = ('claim', 'hmo_provider', 'service_amount', 'hmo_covered_amount', 'platform_processing_fee', 'payment_status', 'date_paid')
    search_fields = ('claim__claim_number', 'hmo_provider__name', 'payment_reference')
    list_filter = ('payment_status', 'hmo_provider', 'date_paid', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Claim & Provider', {
            'fields': ('claim', 'hmo_provider')
        }),
        ('Payment Breakdown', {
            'fields': ('service_amount', 'hmo_covered_amount', 'platform_processing_fee', 'total_due_from_hmo', 'amount_paid')
        }),
        ('Payment Status', {
            'fields': ('payment_status', 'expected_payment_date', 'date_paid', 'payment_reference')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HMOInvoice)
class HMOInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'hmo_provider', 'month', 'year', 'total_claims', 'total_amount_due', 'status', 'date_sent', 'due_date')
    search_fields = ('invoice_number', 'hmo_provider__name')
    list_filter = ('status', 'hmo_provider', 'year', 'month', 'date_sent')
    ordering = ('-year', '-month')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Invoice Information', {
            'fields': ('hmo_provider', 'invoice_number', 'month', 'year', 'status')
        }),
        ('Totals', {
            'fields': ('total_claims', 'total_covered_amount', 'platform_processing_fees', 'total_amount_due', 'amount_paid')
        }),
        ('Dates', {
            'fields': ('date_sent', 'due_date', 'date_paid')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PreAuthorization)
class PreAuthorizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_insurance', 'service_type', 'estimated_cost', 'status', 'requested_date', 'approved_date', 'expiry_date')
    search_fields = ('user_insurance__user__email', 'service_description', 'hmo_reference_number', 'reason')
    list_filter = ('status', 'service_type', 'requested_date', 'approved_date')
    ordering = ('-requested_date',)
    readonly_fields = ('requested_date', 'created_at', 'updated_at')
    fieldsets = (
        ('User & Service', {
            'fields': ('user_insurance', 'service_type', 'service_description', 'estimated_cost', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'hmo_reference_number')
        }),
        ('Dates', {
            'fields': ('requested_date', 'approved_date', 'expiry_date')
        }),
        ('HMO Response', {
            'fields': ('hmo_response', 'approved_amount'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )