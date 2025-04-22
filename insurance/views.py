from rest_framework import generics, permissions
from .models import InsuranceProvider, InsurancePlan, UserInsurance, InsuranceClaim, InsuranceDocument
from .serializers import (
    InsuranceProviderSerializer, InsurancePlanSerializer, UserInsuranceSerializer,
    InsuranceClaimSerializer, InsuranceDocumentSerializer
)

class InsuranceProviderListView(generics.ListAPIView):
    queryset = InsuranceProvider.objects.all()
    serializer_class = InsuranceProviderSerializer
    permission_classes = [permissions.AllowAny]

class InsurancePlanListView(generics.ListAPIView):
    queryset = InsurancePlan.objects.filter(is_active=True)
    serializer_class = InsurancePlanSerializer
    permission_classes = [permissions.AllowAny]

class UserInsuranceListCreateView(generics.ListCreateAPIView):
    serializer_class = UserInsuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserInsurance.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserInsuranceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserInsuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserInsurance.objects.filter(user=self.request.user)

class InsuranceClaimListCreateView(generics.ListCreateAPIView):
    serializer_class = InsuranceClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InsuranceClaim.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InsuranceClaimDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InsuranceClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InsuranceClaim.objects.filter(user=self.request.user)

class InsuranceDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = InsuranceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InsuranceDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InsuranceDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InsuranceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InsuranceDocument.objects.filter(user=self.request.user)