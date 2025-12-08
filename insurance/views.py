# insurance/views.py
from rest_framework import generics, permissions, views, status
from rest_framework.response import Response
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

class VerifyInsuranceDetailsView(views.APIView):
    """
    Verify Member ID and Policy Number with the insurance provider.
    POST /api/insurance/verify/
    Body: { "plan_id": int, "member_id": str, "policy_number": str }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        plan_id = request.data.get('plan_id')
        member_id = request.data.get('member_id')
        policy_number = request.data.get('policy_number')
        
        if not plan_id or not member_id or not policy_number:
            return Response(
                {'error': 'plan_id, member_id, and policy_number are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = InsurancePlan.objects.get(id=plan_id, is_active=True)
        except InsurancePlan.DoesNotExist:
            return Response(
                {'error': 'Invalid insurance plan.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # TODO: Integrate with actual HMO provider API for verification
        # For now, we'll do basic validation:
        # - Check if member_id and policy_number are not empty
        # - Check format (if provider has specific format requirements)
        # - In production, this would call the HMO's verification API
        
        # Basic validation
        if len(member_id.strip()) < 3:
            return Response(
                {
                    'valid': False,
                    'error': 'Member ID appears to be invalid (too short).',
                    'message': 'Please check your Member ID and try again.'
                },
                status=status.HTTP_200_OK
            )
        
        if len(policy_number.strip()) < 3:
            return Response(
                {
                    'valid': False,
                    'error': 'Policy Number appears to be invalid (too short).',
                    'message': 'Please check your Policy Number and try again.'
                },
                status=status.HTTP_200_OK
            )
        
        # Check if this combination already exists for another user
        existing = UserInsurance.objects.filter(
            plan=plan,
            member_id=member_id,
            policy_number=policy_number
        ).exclude(user=request.user).first()
        
        if existing:
            return Response(
                {
                    'valid': False,
                    'error': 'This Member ID and Policy Number combination is already registered to another account.',
                    'message': 'Please verify your details or contact support if you believe this is an error.'
                },
                status=status.HTTP_200_OK
            )
        
        # For now, return a success response with a note that full verification requires HMO API integration
        return Response(
            {
                'valid': True,
                'message': 'Details appear valid. Note: Full verification with HMO provider requires API integration.',
                'provider': plan.provider.name,
                'plan': plan.name,
                'note': 'This is a basic validation. For full verification, please ensure your details match your insurance card.'
            },
            status=status.HTTP_200_OK
        )