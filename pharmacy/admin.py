from django.contrib import admin
from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder

@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'is_24_hours', 'offers_delivery')
    search_fields = ('name', 'address')
    list_filter = ('is_24_hours', 'offers_delivery')
    ordering = ('-created_at',)

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'dosage_form', 'strength', 'requires_prescription')
    search_fields = ('name', 'generic_name')
    list_filter = ('requires_prescription',)
    ordering = ('-created_at',)

@admin.register(PharmacyInventory)
class PharmacyInventoryAdmin(admin.ModelAdmin):
    list_display = ('pharmacy', 'medication', 'in_stock', 'quantity', 'price')
    search_fields = ('pharmacy__name', 'medication__name')
    list_filter = ('in_stock',)
    ordering = ('-last_updated',)

@admin.register(MedicationOrder)
class MedicationOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'pharmacy', 'status', 'is_delivery', 'order_date')
    search_fields = ('user__email', 'pharmacy__name')
    list_filter = ('status', 'is_delivery', 'order_date')
    ordering = ('-order_date',)

@admin.register(MedicationOrderItem)
class MedicationOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'medication', 'quantity', 'price_per_unit', 'total_price')
    search_fields = ('medication__name',)
    ordering = ('-order__order_date',)

@admin.register(MedicationReminder)
class MedicationReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'medication', 'time_of_day', 'frequency', 'is_active')
    search_fields = ('user__email', 'medication__name')
    list_filter = ('frequency', 'is_active')
    ordering = ('-created_at',)