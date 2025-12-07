# doctors/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from django.conf.urls import include
from .views import (
    SpecialtyListView, DoctorListView, DoctorDetailView,
    DoctorReviewListCreateView, DoctorAvailabilityListView,
    DoctorAvailabilityManageViewSet,
    AppointmentListCreateView, AppointmentDetailView,
    PrescriptionListView, PrescriptionDetailView, ForwardPrescriptionView,
    GetTwilioTokenView, DoctorEligibleAppointmentListView,
    DoctorPrescriptionViewSet, DoctorApplicationView, DoctorBankDetailsView, DoctorVerifyBankAccountView,
)
from .video_views import (
    GenerateVideoTokenView, EndVideoSessionView,
    start_virtual_session_enhanced, get_session_recordings, twilio_webhook_room_status
)

router = DefaultRouter()
router.register(r'portal/prescriptions', DoctorPrescriptionViewSet, basename='doctor-portal-prescriptions')
router.register(r'portal/availability', DoctorAvailabilityManageViewSet, basename='doctor-portal-availability')


urlpatterns = [
    path('specialties/', SpecialtyListView.as_view(), name='specialty-list'),
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('<int:doctor_id>/reviews/', DoctorReviewListCreateView.as_view(), name='doctor-review-list-create'),
    path('<int:doctor_id>/availability/', DoctorAvailabilityListView.as_view(), name='doctor-availability'),
    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list-create'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:appointment_id>/token/', GetTwilioTokenView.as_view(), name='get-twilio-token'),
    path('appointments/<int:appointment_id>/video_token/', GetTwilioTokenView.as_view(), name='appointment-video-token'),
    path('appointments/<int:appointment_id>/video/token/', GenerateVideoTokenView.as_view(), name='video-token'),
    path('appointments/<int:appointment_id>/video/end/', EndVideoSessionView.as_view(), name='video-end'),
    
    # Enhanced video endpoints
    path('appointments/<int:appointment_id>/start_virtual/', start_virtual_session_enhanced, name='start-virtual-session'),
    path('appointments/<int:appointment_id>/recordings/', get_session_recordings, name='get-session-recordings'),
    path('video/webhook/room-status/', twilio_webhook_room_status, name='twilio-room-webhook'),
    
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('prescriptions/<int:pk>/forward/', ForwardPrescriptionView.as_view(), name='prescription-forward'),
    
    # Doctor Portal endpoints
    path('portal/eligible-appointments-for-prescription/', DoctorEligibleAppointmentListView.as_view(), name='doctor-eligible-appointments'),
    path('portal/application/', DoctorApplicationView.as_view(), name='doctor-application'),
    path('portal/onboarding/bank/', DoctorBankDetailsView.as_view(), name='doctor-bank-details'),
    path('portal/verify-account/', DoctorVerifyBankAccountView.as_view(), name='doctor-verify-account'),
    
    path('<int:doctor_id>/eligible-appointments/', DoctorEligibleAppointmentListView.as_view(), name='doctor-eligible-appointments-legacy'),
    path('', include(router.urls)),
]