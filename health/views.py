from rest_framework import generics, permissions, views
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from notifications.utils import create_notification
from .models import VitalSign, FoodLog, ExerciseLog, SleepLog, HealthGoal, MedicalDocument, WaterIntakeLog, HealthInsight
from .serializers import (
    VitalSignSerializer, VitalSignWithAlertsSerializer, FoodLogSerializer,
    ExerciseLogSerializer, SleepLogSerializer, HealthGoalSerializer, MedicalDocumentSerializer,
    WaterIntakeLogSerializer, HealthInsightSerializer
)

from .permissions import IsOwnerOrSharedWith
from .services import HealthAnalyticsService

# ... (Previous views remain, I'll re-include them for completeness)

class MedicalDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicalDocument.objects.filter(user=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        """Set user/uploaded_by and notify doctor if linked to appointment or test request."""
        # Handle test_request_id if provided
        test_request_id = serializer.validated_data.pop('test_request_id', None)
        test_request = None
        
        if test_request_id:
            from doctors.models import TestRequest, Appointment
            try:
                test_request = TestRequest.objects.get(id=test_request_id, patient=self.request.user)
                
                # If followup_appointment is not set, try to find the most recent follow-up appointment
                # that was created for this test request (by checking original_appointment)
                if not test_request.followup_appointment:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Test request {test_request_id} has no followup_appointment. Attempting to find one...")
                    
                    # Try multiple strategies to find the follow-up appointment
                    followup_appt = None
                    
                    # Strategy 1: Find by original_appointment matching test request's appointment
                    if test_request.appointment:
                        logger.info(f"Strategy 1: Looking for appointments with original_appointment={test_request.appointment.id}, user={self.request.user.id}")
                        
                        # Try with is_followup=True first
                        followup_appt = Appointment.objects.filter(
                            user=self.request.user,
                            original_appointment=test_request.appointment,
                            is_followup=True
                        ).order_by('-created_at').first()
                        
                        # If not found, try without is_followup filter
                        if not followup_appt:
                            followup_appt = Appointment.objects.filter(
                                user=self.request.user,
                                original_appointment=test_request.appointment
                            ).order_by('-created_at').first()
                    
                    # Strategy 2: Find any recent appointment with the same doctor (more lenient)
                    if not followup_appt and test_request.doctor:
                        logger.info(f"Strategy 2: Looking for recent appointments with doctor={test_request.doctor.id}, user={self.request.user.id}")
                        doctor_id = test_request.doctor.id if hasattr(test_request.doctor, 'id') else test_request.doctor
                        followup_appt = Appointment.objects.filter(
                            user=self.request.user,
                            doctor_id=doctor_id,
                            status__in=['scheduled', 'confirmed']
                        ).order_by('-created_at').first()
                    
                    # Strategy 3: If appointment_id is provided in the request, use that
                    appointment_id = serializer.validated_data.get('appointment')
                    if not followup_appt and appointment_id:
                        logger.info(f"Strategy 3: Using provided appointment_id={appointment_id}")
                        try:
                            followup_appt = Appointment.objects.get(
                                id=appointment_id,
                                user=self.request.user
                            )
                        except Appointment.DoesNotExist:
                            pass
                    
                    if followup_appt:
                        # Link it automatically
                        test_request.followup_appointment = followup_appt
                        test_request.save()
                        logger.info(f"Auto-linked test request {test_request_id} to appointment {followup_appt.id}")
                    else:
                        # If we still can't find it, allow the upload anyway but log a warning
                        logger.warning(f"Could not find follow-up appointment for test request {test_request_id}, but allowing upload to proceed")
                        # Don't raise error - allow upload to proceed
            except TestRequest.DoesNotExist:
                pass  # Continue without linking if invalid
        
        document = serializer.save(
            user=self.request.user,
            uploaded_by=self.request.user,
            test_request=test_request
        )
        
        patient = self.request.user
        
        # Notify doctor if linked to test request
        if test_request and test_request.doctor:
            doctor_user = test_request.doctor.user if hasattr(test_request.doctor, 'user') else None
            if doctor_user:
                # Update test request status to completed if results uploaded
                if test_request.status == 'pending':
                    from django.utils import timezone
                    test_request.status = 'completed'
                    test_request.completed_at = timezone.now()
                    test_request.save()
                
                filename = document.file.name.split('/')[-1] if document.file else 'document'
                create_notification(
                    recipient=doctor_user,
                    actor=patient,
                    verb=f"Patient {patient.get_full_name() or patient.username} uploaded test results for '{test_request.test_name}': {filename}",
                    title=f"Test Results Uploaded: {test_request.test_name}",
                    level='success',
                    category='test_request',
                    action_url=f"/portal/test-requests/{test_request.id}",
                    action_text="View Test Results"
                )
        
        # Notify doctor if linked to appointment (existing functionality)
        elif document.appointment and document.appointment.doctor:
            doctor_user = document.appointment.doctor.user if hasattr(document.appointment.doctor, 'user') else None
            if doctor_user:
                filename = document.file.name.split('/')[-1] if document.file else 'document'
                create_notification(
                    recipient=doctor_user,
                    actor=patient,
                    verb=f"Patient {patient.get_full_name() or patient.username} uploaded a document ('{filename}') for appointment on {document.appointment.date.strftime('%b %d')}.",
                    title=f"New Document Uploaded",
                    level='info',
                    category='appointment',
                    action_url=f"/portal/appointments/{document.appointment.id}/documents/",
                    action_text="View Document"
                )

class MedicalDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSharedWith]

    def get_queryset(self):
        return MedicalDocument.objects.filter(user=self.request.user)

class VitalSignListCreateView(generics.ListCreateAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'date_recorded': ['gte', 'lte'],
    }
    ordering_fields = ['date_recorded']
    ordering = ['-date_recorded']

    def get_queryset(self):
        return VitalSign.objects.filter(user=self.request.user).order_by('-date_recorded')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VitalSignDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VitalSign.objects.filter(user=self.request.user)

class VitalSignLatestView(generics.RetrieveAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return VitalSign.objects.filter(user=self.request.user).order_by('-date_recorded').first()


class PatientVitalSignsView(generics.ListAPIView):
    """
    Endpoint for doctors to view a patient's vital signs.
    GET /api/health/patients/<user_id>/vital-signs/
    Query params:
        - days: Number of days to look back (default: 30)
    """
    serializer_class = VitalSignWithAlertsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from datetime import timedelta
        from django.utils import timezone
        
        # Check if user is a doctor
        if not hasattr(self.request.user, 'doctor_profile'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only doctors can view patient vitals.")
        
        user_id = self.kwargs.get('user_id')
        days = int(self.request.query_params.get('days', 30))
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return VitalSign.objects.filter(
            user_id=user_id,
            date_recorded__gte=cutoff_date
        ).order_by('-date_recorded')

class FoodLogListCreateView(generics.ListCreateAPIView):
    serializer_class = FoodLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FoodLog.objects.filter(user=self.request.user).order_by('-datetime')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FoodLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FoodLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FoodLog.objects.filter(user=self.request.user)

class ExerciseLogListCreateView(generics.ListCreateAPIView):
    serializer_class = ExerciseLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'datetime': ['gte', 'lte'],
    }
    ordering = ['-datetime']

    def get_queryset(self):
        return ExerciseLog.objects.filter(user=self.request.user).order_by('-datetime')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExerciseLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExerciseLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExerciseLog.objects.filter(user=self.request.user)

class SleepLogListCreateView(generics.ListCreateAPIView):
    serializer_class = SleepLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'sleep_time': ['gte', 'lte'],
    }
    ordering = ['-sleep_time']

    def get_queryset(self):
        return SleepLog.objects.filter(user=self.request.user).order_by('-sleep_time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SleepLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SleepLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SleepLog.objects.filter(user=self.request.user)

class HealthGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = HealthGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class HealthGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HealthGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthGoal.objects.filter(user=self.request.user)

class WaterIntakeLogListCreateView(generics.ListCreateAPIView):
    serializer_class = WaterIntakeLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WaterIntakeLog.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WaterIntakeTodayView(generics.RetrieveAPIView):
    serializer_class = WaterIntakeLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        from django.utils import timezone
        return WaterIntakeLog.objects.filter(
            user=self.request.user, 
            date=timezone.now().date()
        ).first()

class HealthInsightListView(generics.ListAPIView):
    serializer_class = HealthInsightSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthInsight.objects.filter(user=self.request.user).order_by('-created_at')

class WeeklySummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        summary = HealthAnalyticsService.generate_weekly_summary(request.user)
        return Response(summary)
