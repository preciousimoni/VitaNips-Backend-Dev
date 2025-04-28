from rest_framework import generics, permissions
from notifications.utils import create_notification
from .models import VitalSign, SymptomLog, FoodLog, ExerciseLog, SleepLog, HealthGoal, MedicalDocument
from .serializers import (
    VitalSignSerializer, SymptomLogSerializer, FoodLogSerializer,
    ExerciseLogSerializer, SleepLogSerializer, HealthGoalSerializer, MedicalDocumentSerializer
)
from .permissions import IsOwnerOrAssociatedDoctorReadOnly

class MedicalDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ... lists docs for request.user ...
        return MedicalDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user/uploaded_by and notify doctor if linked to appointment."""
        # Assuming uploaded_by should always be the request user here
        document = serializer.save(user=self.request.user, uploaded_by=self.request.user)

        # Check if the document is linked to an appointment
        if document.appointment and document.appointment.doctor:
            doctor_user = document.appointment.doctor.user if hasattr(document.appointment.doctor, 'user') else None
            patient = self.request.user

            if doctor_user: # Only notify if the doctor has a user account
                create_notification(
                    recipient=doctor_user,
                    actor=patient,
                    verb=f"Patient {patient.first_name} {patient.last_name} uploaded a document ('{document.filename or 'document'}') for appointment on {document.appointment.date.strftime('%b %d')}.",
                    level='info', # Or a specific 'document' level
                    target_url=f"/portal/appointments/{document.appointment.id}/documents/" # Example doctor portal URL
                )
                print(f"Document upload notification created for doctor {doctor_user.id} for document {document.id}")

class MedicalDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssociatedDoctorReadOnly]

    def get_queryset(self):
        return MedicalDocument.objects.filter(user=self.request.user)

class VitalSignListCreateView(generics.ListCreateAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VitalSign.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VitalSignDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VitalSign.objects.filter(user=self.request.user)

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