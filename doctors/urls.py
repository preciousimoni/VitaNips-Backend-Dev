# doctors/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from django.conf.urls import include
from .views import (
    SpecialtyListView, DoctorListView, DoctorDetailView,
    DoctorReviewListCreateView, DoctorAvailabilityListView,
    AppointmentListCreateView, AppointmentDetailView,
    PrescriptionListView, PrescriptionDetailView, ForwardPrescriptionView,
    GetTwilioTokenView, DoctorEligibleAppointmentListView,
    DoctorPrescriptionViewSet,
)

router = DefaultRouter()
router.register(r'doctor-prescriptions', DoctorPrescriptionViewSet, basename='doctor-prescriptions')


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
    path('prescriptions/<int:pk>/forward/', ForwardPrescriptionView.as_view(), name='prescription-forward'),
    path('<int:doctor_id>/eligible-appointments/', DoctorEligibleAppointmentListView.as_view(), name='doctor-eligible-appointments'),
    path('', include(router.urls)),
]