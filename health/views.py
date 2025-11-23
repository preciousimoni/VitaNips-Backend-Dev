from rest_framework import generics, permissions, views
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from notifications.utils import create_notification
from .models import VitalSign, SymptomLog, FoodLog, ExerciseLog, SleepLog, HealthGoal, MedicalDocument, WaterIntakeLog, HealthInsight
from .serializers import (
    VitalSignSerializer, SymptomLogSerializer, FoodLogSerializer,
    ExerciseLogSerializer, SleepLogSerializer, HealthGoalSerializer, MedicalDocumentSerializer,
    WaterIntakeLogSerializer, HealthInsightSerializer
)
from .permissions import IsOwnerOrAssociatedDoctorReadOnly
from .services import HealthAnalyticsService

# ... (Previous views remain, I'll re-include them for completeness)

class MedicalDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicalDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user/uploaded_by and notify doctor if linked to appointment."""
        document = serializer.save(user=self.request.user, uploaded_by=self.request.user)

        if document.appointment and document.appointment.doctor:
            doctor_user = document.appointment.doctor.user if hasattr(document.appointment.doctor, 'user') else None
            patient = self.request.user

            if doctor_user:
                create_notification(
                    recipient=doctor_user,
                    actor=patient,
                    verb=f"Patient {patient.first_name} {patient.last_name} uploaded a document ('{document.file.name or 'document'}') for appointment on {document.appointment.date.strftime('%b %d')}.",
                    level='info',
                    target_url=f"/portal/appointments/{document.appointment.id}/documents/"
                )

class MedicalDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssociatedDoctorReadOnly]

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
        return VitalSign.objects.filter(user=self.request.user)

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

class SymptomLogListCreateView(generics.ListCreateAPIView):
    serializer_class = SymptomLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SymptomLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SymptomLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SymptomLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SymptomLog.objects.filter(user=self.request.user)

class FoodLogListCreateView(generics.ListCreateAPIView):
    serializer_class = FoodLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FoodLog.objects.filter(user=self.request.user)

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
        return ExerciseLog.objects.filter(user=self.request.user)

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
        return SleepLog.objects.filter(user=self.request.user)

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
        return HealthInsight.objects.filter(user=self.request.user)

class WeeklySummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        summary = HealthAnalyticsService.generate_weekly_summary(request.user)
        return Response(summary)
