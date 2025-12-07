from django.contrib import admin
from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder, MedicationLog

@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'is_24_hours', 'offers_delivery', 'is_active', 'created_at')
    search_fields = ('name', 'address', 'phone_number', 'email')
    list_filter = ('is_24_hours', 'offers_delivery', 'is_active', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'phone_number', 'email', 'operating_hours')
        }),
        ('Services', {
            'fields': ('is_24_hours', 'offers_delivery', 'is_active')
        }),
        ('Location', {
            'fields': ('location',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'dosage_form', 'strength', 'manufacturer', 'requires_prescription', 'created_at')
    search_fields = ('name', 'generic_name', 'manufacturer', 'description')
    list_filter = ('requires_prescription', 'dosage_form', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'description', 'manufacturer')
        }),
        ('Dosage & Form', {
            'fields': ('dosage_form', 'strength', 'requires_prescription')
        }),
        ('Additional Information', {
            'fields': ('side_effects', 'contraindications', 'storage_instructions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PharmacyInventory)
class PharmacyInventoryAdmin(admin.ModelAdmin):
    list_display = ('pharmacy', 'medication', 'in_stock', 'quantity', 'price', 'last_updated')
    search_fields = ('pharmacy__name', 'medication__name', 'medication__generic_name')
    list_filter = ('in_stock', 'last_updated')
    ordering = ('-last_updated',)
    readonly_fields = ('last_updated',)

@admin.register(MedicationOrder)
class MedicationOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'pharmacy', 'status', 'is_delivery', 'total_amount', 'payment_status', 'order_date')
    search_fields = ('user__email', 'pharmacy__name', 'payment_reference', 'delivery_address')
    list_filter = ('status', 'is_delivery', 'payment_status', 'insurance_claim_generated', 'order_date')
    ordering = ('-order_date',)
    readonly_fields = ('order_date',)
    fieldsets = (
        ('Order Details', {
            'fields': ('user', 'pharmacy', 'prescription', 'status', 'order_date', 'pickup_or_delivery_date', 'notes')
        }),
        ('Delivery Information', {
            'fields': ('is_delivery', 'delivery_address')
        }),
        ('Financial Information', {
            'fields': ('total_amount', 'payment_reference', 'payment_status')
        }),
        ('Insurance Information', {
            'fields': ('user_insurance', 'insurance_covered_amount', 'patient_copay', 'insurance_claim_generated'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MedicationOrderItem)
class MedicationOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'prescription_item', 'medication_name_text', 'dosage_text', 'quantity', 'price_per_unit', 'total_price')
    search_fields = ('medication_name_text', 'dosage_text', 'order__user__email')
    list_filter = ('order__status', 'order__order_date')
    ordering = ('-order__order_date',)
    fieldsets = (
        ('Item Details', {
            'fields': ('order', 'prescription_item', 'medication_name_text', 'dosage_text', 'quantity', 'price_per_unit')
        }),
    )

@admin.register(MedicationReminder)
class MedicationReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'medication', 'prescription_item', 'start_date', 'end_date', 'time_of_day', 'frequency', 'is_active', 'created_at')
    search_fields = ('user__email', 'medication__name', 'dosage', 'notes')
    list_filter = ('frequency', 'is_active', 'start_date', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Reminder Details', {
            'fields': ('user', 'medication', 'prescription_item', 'is_active')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'time_of_day', 'frequency', 'custom_frequency')
        }),
        ('Dosage Information', {
            'fields': ('dosage', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    list_display = ('reminder', 'scheduled_time', 'taken_at', 'status', 'created_at')
    search_fields = ('reminder__medication__name', 'reminder__user__email', 'notes')
    list_filter = ('status', 'scheduled_time', 'created_at')
    ordering = ('-scheduled_time',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Log Details', {
            'fields': ('reminder', 'scheduled_time', 'taken_at', 'status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )