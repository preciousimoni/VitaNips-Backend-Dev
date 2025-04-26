from rest_framework import generics, permissions
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
        return MedicalDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, uploaded_by=self.request.user)

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