from django.contrib import admin
from .models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument

@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_phone', 'website', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'plan_type', 'monthly_premium', 'is_active')
    search_fields = ('name', 'provider__name')
    list_filter = ('plan_type', 'is_active')
    ordering = ('-created_at',)

@admin.register(UserInsurance)
class UserInsuranceAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'policy_number', 'start_date', 'is_primary')
    search_fields = ('user__email', 'plan__name')
    list_filter = ('is_primary', 'start_date')
    ordering = ('-created_at',)

@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ('user', 'claim_number', 'service_date', 'status', 'claimed_amount')
    search_fields = ('user__email', 'claim_number')
    list_filter = ('status', 'service_date')
    ordering = ('-date_submitted',)

@admin.register(InsuranceDocument)
class InsuranceDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'document_type', 'date_uploaded')
    search_fields = ('user__email', 'title')
    list_filter = ('document_type', 'date_uploaded')
    ordering = ('-date_uploaded',)