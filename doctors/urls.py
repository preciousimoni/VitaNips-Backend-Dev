from django.urls import path
from .views import (
    SpecialtyListView, DoctorListView, DoctorDetailView,
    DoctorReviewListCreateView, DoctorAvailabilityListView,
    AppointmentListCreateView, AppointmentDetailView,
    PrescriptionListView, PrescriptionDetailView,
    GetTwilioTokenView
)

urlpatterns = [
    path('specialties/', SpecialtyListView.as_view(), name='specialty-list'),
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:doctor_id>/reviews/', DoctorReviewListCreateView.as_view(), name='doctor-reviews'),
    path('<int:doctor_id>/availability/', DoctorAvailabilityListView.as_view(), name='doctor-availability'),
    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:appointment_id>/video_token/', GetTwilioTokenView.as_view(), name='appointment-video-token'),
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
]