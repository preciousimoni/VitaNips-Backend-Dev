# pharmacy/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PharmacyListView, PharmacyOrderListView, PharmacyOrderDetailView,
    MedicationListView, PharmacyInventoryListView, MedicationOrderListCreateView,
    MedicationOrderDetailView, ConfirmPickupView, MedicationReminderListCreateView, MedicationReminderDetailView,
    CreateOrderFromPrescriptionView, PharmacyDetailView,
    MedicationLogListCreateView, LogMedicationIntakeView,
    PharmacyInventoryPortalViewSet
)

router = DefaultRouter()
router.register(r'portal/inventory', PharmacyInventoryPortalViewSet, basename='pharmacy-portal-inventory')

urlpatterns = [
    path('', PharmacyListView.as_view(), name='pharmacy-list'),
    path('<int:pk>/', PharmacyDetailView.as_view(), name='pharmacy-detail'),
    path('medications/', MedicationListView.as_view(), name='medication-list'),
    path('<int:pharmacy_id>/inventory/', PharmacyInventoryListView.as_view(), name='pharmacy-inventory'),
    path('portal/orders/', PharmacyOrderListView.as_view(), name='pharmacy-order-list'),
    path('portal/orders/<int:pk>/', PharmacyOrderDetailView.as_view(), name='pharmacy-order-detail'),
    path('prescriptions/<int:prescription_id>/create_order/', CreateOrderFromPrescriptionView.as_view(), name='prescription-create-order'),
    path('orders/', MedicationOrderListCreateView.as_view(), name='medication-order-list'),
    path('orders/<int:pk>/', MedicationOrderDetailView.as_view(), name='medication-order-detail'),
    path('orders/<int:pk>/confirm_pickup/', ConfirmPickupView.as_view(), name='medication-order-confirm-pickup'),
    path('reminders/', MedicationReminderListCreateView.as_view(), name='medication-reminder-list'),
    path('reminders/<int:pk>/', MedicationReminderDetailView.as_view(), name='medication-reminder-detail'),
    path('logs/', MedicationLogListCreateView.as_view(), name='medication-log-list'),
    path('reminders/<int:reminder_id>/log/', LogMedicationIntakeView.as_view(), name='medication-log-intake'),
    path('', include(router.urls)),  # Include router URLs for portal inventory
]