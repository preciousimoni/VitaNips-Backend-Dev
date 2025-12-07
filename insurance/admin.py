from django.contrib import admin
from .models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument

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
    list_display = ('name', 'provider', 'plan_type', 'monthly_premium', 'annual_deductible', 'out_of_pocket_max', 'is_active', 'created_at')
    search_fields = ('name', 'provider__name', 'description', 'coverage_details')
    list_filter = ('plan_type', 'is_active', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Plan Information', {
            'fields': ('provider', 'name', 'plan_type', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('monthly_premium', 'annual_deductible', 'out_of_pocket_max')
        }),
        ('Coverage Details', {
            'fields': ('coverage_details',)
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