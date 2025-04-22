from django.urls import path
from .views import (
    SpecialtyListView, DoctorListView, DoctorDetailView,
    DoctorReviewListCreateView, DoctorAvailabilityListView,
    AppointmentListCreateView, AppointmentDetailView, PrescriptionListView
)

urlpatterns = [
    path('specialties/', SpecialtyListView.as_view(), name='specialty-list'),
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:doctor_id>/reviews/', DoctorReviewListCreateView.as_view(), name='doctor-reviews'),
    path('<int:doctor_id>/availability/', DoctorAvailabilityListView.as_view(), name='doctor-availability'),
    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
]