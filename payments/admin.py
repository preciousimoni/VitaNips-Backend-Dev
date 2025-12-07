from django.contrib import admin
from .models import (
    SubscriptionPlan, UserSubscription, DoctorSubscription,
    DoctorSubscriptionRecord, Transaction, RevenueReport
)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'monthly_price', 'annual_price', 'max_appointments_per_month', 'max_family_members', 'is_active', 'created_at')
    search_fields = ('name', 'tier', 'description')
    list_filter = ('tier', 'is_active', 'created_at')
    ordering = ('monthly_price',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'tier', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('monthly_price', 'annual_price')
        }),
        ('Limits', {
            'fields': ('max_appointments_per_month', 'max_family_members')
        }),
        ('Features', {
            'fields': ('features',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'billing_cycle', 'current_period_start', 'current_period_end', 'auto_renew', 'created_at')
    search_fields = ('user__email', 'plan__name', 'payment_reference')
    list_filter = ('status', 'billing_cycle', 'auto_renew', 'started_at', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'is_active', 'price')
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'plan', 'status', 'billing_cycle', 'auto_renew')
        }),
        ('Period Information', {
            'fields': ('started_at', 'current_period_start', 'current_period_end', 'cancelled_at')
        }),
        ('Payment', {
            'fields': ('payment_reference',)
        }),
        ('Computed Fields', {
            'fields': ('is_active', 'price'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DoctorSubscription)
class DoctorSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'monthly_price', 'max_appointments_per_month', 'is_active', 'created_at')
    search_fields = ('name', 'tier', 'description')
    list_filter = ('tier', 'is_active', 'created_at')
    ordering = ('monthly_price',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'tier', 'description', 'is_active')
        }),
        ('Pricing & Limits', {
            'fields': ('monthly_price', 'max_appointments_per_month')
        }),
        ('Features', {
            'fields': ('features',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DoctorSubscriptionRecord)
class DoctorSubscriptionRecordAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'plan', 'status', 'current_period_start', 'current_period_end', 'auto_renew', 'created_at')
    search_fields = ('doctor__first_name', 'doctor__last_name', 'plan__name', 'payment_reference')
    list_filter = ('status', 'auto_renew', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'is_active')
    fieldsets = (
        ('Subscription Details', {
            'fields': ('doctor', 'plan', 'status', 'auto_renew')
        }),
        ('Period Information', {
            'fields': ('current_period_start', 'current_period_end')
        }),
        ('Payment', {
            'fields': ('payment_reference',)
        }),
        ('Computed Fields', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'transaction_type', 'gross_amount', 'platform_commission', 'net_amount', 'status', 'payment_gateway', 'currency', 'created_at', 'completed_at')
    search_fields = ('transaction_id', 'reference', 'user__email', 'payment_method')
    list_filter = ('transaction_type', 'status', 'payment_gateway', 'currency', 'created_at', 'completed_at')
    ordering = ('-created_at',)
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'transaction_type', 'reference', 'status')
        }),
        ('User & Related Object', {
            'fields': ('user', 'related_object_id', 'related_object_type')
        }),
        ('Financial Information', {
            'fields': ('gross_amount', 'platform_commission', 'net_amount', 'currency')
        }),
        ('Payment Information', {
            'fields': ('payment_gateway', 'payment_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RevenueReport)
class RevenueReportAdmin(admin.ModelAdmin):
    list_display = ('period_type', 'period_start', 'period_end', 'total_gross_revenue', 'total_platform_commission', 'total_transactions', 'successful_transactions', 'created_at')
    search_fields = ('period_type',)
    list_filter = ('period_type', 'period_start', 'created_at')
    ordering = ('-period_start',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Period Information', {
            'fields': ('period_type', 'period_start', 'period_end')
        }),
        ('Revenue Breakdown', {
            'fields': (
                'total_gross_revenue',
                'total_platform_commission',
                'total_subscription_revenue',
                'total_premium_feature_revenue',
            )
        }),
        ('Revenue by Type', {
            'fields': (
                'appointment_revenue',
                'medication_order_revenue',
                'virtual_session_revenue',
            )
        }),
        ('Transaction Counts', {
            'fields': (
                'total_transactions',
                'successful_transactions',
                'failed_transactions',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

