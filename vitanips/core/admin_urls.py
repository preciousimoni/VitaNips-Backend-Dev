# vitanips/core/admin_urls.py
from django.urls import path
from .admin_views import (
    AdminStatsView,
    AdminUsersListView,
    AdminUserDetailView,
    AdminDoctorsListView,
    AdminDoctorVerificationView,
    AdminPharmaciesListView,
    AdminPharmacyDetailView,
    AdminAnalyticsView,
    AdminAppointmentsListView,
    AdminAppointmentDetailView,
    AdminRecentActivityView,
)

urlpatterns = [
    # Stats
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
    
    # Users Management
    path('users/', AdminUsersListView.as_view(), name='admin-users-list'),
    path('users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    
    # Doctors Management
    path('doctors/', AdminDoctorsListView.as_view(), name='admin-doctors-list'),
    path('doctors/<int:doctor_id>/verify/', AdminDoctorVerificationView.as_view(), name='admin-doctor-verify'),
    
    # Pharmacies Management
    path('pharmacies/', AdminPharmaciesListView.as_view(), name='admin-pharmacies-list'),
    path('pharmacies/<int:pharmacy_id>/', AdminPharmacyDetailView.as_view(), name='admin-pharmacy-detail'),
    
    # Analytics
    path('analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
    
    # Appointments Management
    path('appointments/', AdminAppointmentsListView.as_view(), name='admin-appointments-list'),
    path('appointments/<int:appointment_id>/', AdminAppointmentDetailView.as_view(), name='admin-appointment-detail'),
    
    # Recent Activity
    path('activity/', AdminRecentActivityView.as_view(), name='admin-recent-activity'),
]
