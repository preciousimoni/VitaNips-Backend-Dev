# users/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserUpdateSerializer,
    MedicalHistorySerializer, VaccinationSerializer
)
from .models import MedicalHistory, Vaccination
from emergency.models import EmergencyContact
from emergency.serializers import EmergencyContactSerializer
from .permissions import IsOwner

User = get_user_model()

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Prefetch related objects to avoid N+1 queries
        return User.objects.prefetch_related(
            'emergency_contacts',
            'insurance_plans',  # UserInsurance related_name
            'vaccinations'  # Vaccination related_name
        ).get(pk=self.request.user.pk)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

class MedicalHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicalHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicalHistory.objects.filter(user=self.request.user)

class VaccinationListCreateView(generics.ListCreateAPIView):
    serializer_class = VaccinationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vaccination.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VaccinationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VaccinationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vaccination.objects.filter(user=self.request.user)

class EmergencyContactListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)
