from django.urls import path
from .views import (
    EmergencyServiceListView, EmergencyContactListCreateView, EmergencyContactDetailView,
    EmergencyAlertListCreateView, EmergencyAlertDetailView
)

urlpatterns = [
    path('services/', EmergencyServiceListView.as_view(), name='emergency-service-list'),
    path('contacts/', EmergencyContactListCreateView.as_view(), name='emergency-contact-list'),
    path('contacts/<int:pk>/', EmergencyContactDetailView.as_view(), name='emergency-contact-detail'),
    path('alerts/', EmergencyAlertListCreateView.as_view(), name='emergency-alert-list'),
    path('alerts/<int:pk>/', EmergencyAlertDetailView.as_view(), name='emergency-alert-detail'),
]