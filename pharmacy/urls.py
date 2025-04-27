from django.urls import path
from .views import (
    PharmacyListView, MedicationListView, PharmacyInventoryListView,
    MedicationOrderListCreateView, MedicationOrderDetailView,
    MedicationReminderListCreateView, MedicationReminderDetailView,
    CreateOrderFromPrescriptionView
)

urlpatterns = [
    path('', PharmacyListView.as_view(), name='pharmacy-list'),
    path('medications/', MedicationListView.as_view(), name='medication-list'),
    path('<int:pharmacy_id>/inventory/', PharmacyInventoryListView.as_view(), name='pharmacy-inventory'),
    path('prescriptions/<int:prescription_id>/create_order/', CreateOrderFromPrescriptionView.as_view(), name='prescription-create-order'),
    path('orders/', MedicationOrderListCreateView.as_view(), name='medication-order-list'),
    path('orders/<int:pk>/', MedicationOrderDetailView.as_view(), name='medication-order-detail'),
    path('reminders/', MedicationReminderListCreateView.as_view(), name='medication-reminder-list'),
    path('reminders/<int:pk>/', MedicationReminderDetailView.as_view(), name='medication-reminder-detail'),
]