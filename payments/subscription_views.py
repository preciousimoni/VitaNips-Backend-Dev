# payments/subscription_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    SubscriptionPlan, UserSubscription, 
    DoctorSubscription, DoctorSubscriptionRecord,
    PharmacySubscription, PharmacySubscriptionRecord
)
from .services import flutterwave_service
from .commission_service import get_commission_breakdown
import logging
import uuid

logger = logging.getLogger(__name__)


class SubscriptionPlanListView(ListAPIView):
    """List all available subscription plans"""
    permission_classes = [AllowAny]  # Allow anyone to view plans (no auth required)
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    pagination_class = None  # Disable pagination for subscription plans
    
    def get_serializer_class(self):
        from .serializers import SubscriptionPlanSerializer
        return SubscriptionPlanSerializer


class UserSubscriptionView(RetrieveAPIView):
    """Get current user's subscription"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        subscription = UserSubscription.objects.filter(
            user=self.request.user,
            status='active'
        ).first()
        return subscription
    
    def get_serializer_class(self):
        from .serializers import UserSubscriptionSerializer
        return UserSubscriptionSerializer


class SubscribeView(APIView):
    """Subscribe to a plan"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Subscribe to a subscription plan
        
        Expected payload:
        {
            "plan_id": 1,
            "billing_cycle": "monthly" | "annual"
        }
        """
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Subscription plan not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate price
        if billing_cycle == 'annual' and plan.annual_price:
            price = plan.annual_price
            period_days = 365
        else:
            price = plan.monthly_price
            period_days = 30
        
        # Cancel existing active subscription
        UserSubscription.objects.filter(
            user=request.user,
            status='active'
        ).update(status='cancelled', cancelled_at=timezone.now())
        
        # Create new subscription
        now = timezone.now()
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            billing_cycle=billing_cycle,
            current_period_start=now,
            current_period_end=now + timedelta(days=period_days),
            status='active'
        )
        
        # Initialize payment
        reference = f"subscription_{subscription.id}_{subscription.user.id}"
        try:
            result = flutterwave_service.initialize_transaction(
                email=request.user.email,
                amount=price,
                reference=reference,
                metadata={
                    'user_id': request.user.id,
                    'subscription_id': subscription.id,
                    'plan_id': plan.id,
                    'billing_cycle': billing_cycle
                }
            )
            
            if result.get('status') == 'success':
                subscription.payment_reference = reference
                subscription.save()
                
                return Response({
                    'subscription_id': subscription.id,
                    'plan': plan.name,
                    'billing_cycle': billing_cycle,
                    'amount': str(price),
                    'payment_url': result['data']['link'],
                    'reference': reference
                }, status=status.HTTP_200_OK)
            else:
                subscription.status = 'cancelled'
                subscription.save()
                return Response(
                    {'error': 'Failed to initialize payment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Subscription payment error: {e}")
            subscription.status = 'cancelled'
            subscription.save()
            return Response(
                {'error': f'Payment initialization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CancelSubscriptionView(APIView):
    """Cancel current subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if not subscription:
            return Response(
                {'error': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.auto_renew = False
        subscription.save()
        
        return Response({
            'message': 'Subscription cancelled successfully',
            'subscription_end_date': subscription.current_period_end
        }, status=status.HTTP_200_OK)


class CheckSubscriptionStatusView(APIView):
    """Check if user has active premium subscription"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = UserSubscription.objects.filter(
                user=request.user,
                status='active'
            ).select_related('plan').first()
            
            if subscription and subscription.is_active:
                return Response({
                    'has_premium': True,
                    'plan': subscription.plan.tier,
                    'plan_name': subscription.plan.name,
                    'expires_at': subscription.current_period_end
                })
            else:
                # Calculate remaining free appointments
                # Count lifetime appointments for this user
                from doctors.models import Appointment
                from django.conf import settings
                
                appointment_count = Appointment.objects.filter(
                    user=request.user
                ).count()
                
                free_limit = getattr(settings, 'FREEMIUM_APPOINTMENT_LIMIT', 3)
                remaining = max(0, free_limit - appointment_count)
                
                return Response({
                    'has_premium': False,
                    'plan': 'free',
                    'remaining_free_appointments': remaining,
                    'total_appointments': appointment_count,
                    'free_limit': free_limit
                })
        except Exception as e:
            logger.error(f"Error checking subscription status for user {request.user.id}: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to check subscription status', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PharmacySubscriptionView(APIView):
    """Manage pharmacy subscription"""
    permission_classes = [IsAuthenticated]
    
    def get_pharmacy(self, user):
        if not user.is_pharmacy_staff or not hasattr(user, 'works_at_pharmacy'):
            return None
        return user.works_at_pharmacy

    def get(self, request):
        pharmacy = self.get_pharmacy(request.user)
        if not pharmacy:
            return Response(
                {'error': 'User is not associated with a pharmacy'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        subscription = PharmacySubscriptionRecord.objects.filter(
            pharmacy=pharmacy,
            status='active'
        ).first()
        
        if not subscription:
            return Response({'status': 'inactive', 'message': 'No active subscription found'})
            
        from .serializers import PharmacySubscriptionRecordSerializer
        serializer = PharmacySubscriptionRecordSerializer(subscription)
        return Response(serializer.data)

    def post(self, request):
        """
        Renew or subscribe to a pharmacy plan.
        Payload: { "plan_id": 1 }
        """
        pharmacy = self.get_pharmacy(request.user)
        if not pharmacy:
            return Response(
                {'error': 'User is not associated with a pharmacy'},
                status=status.HTTP_403_FORBIDDEN
            )

        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'error': 'plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = PharmacySubscription.objects.get(id=plan_id, is_active=True)
        except PharmacySubscription.DoesNotExist:
            return Response({'error': 'Invalid plan ID'}, status=status.HTTP_404_NOT_FOUND)

        # In a real implementation, we would initialize a payment here.
        # For now, we'll mock a successful subscription for development.
        
        # Cancel existing active subscription
        PharmacySubscriptionRecord.objects.filter(
            pharmacy=pharmacy,
            status='active'
        ).update(status='cancelled')
        
        now = timezone.now()
        # Create pending subscription
        subscription = PharmacySubscriptionRecord.objects.create(
            pharmacy=pharmacy,
            plan=plan,
            current_period_start=now,
            current_period_end=now + timedelta(days=365), # Annual subscription
            status='pending'
        )
        
        # Initialize payment
        reference = f"pharmacy_subscription_{subscription.id}_{uuid.uuid4().hex[:8]}"
        try:
            result = flutterwave_service.initialize_transaction(
                email=pharmacy.email or request.user.email,
                amount=plan.annual_price,
                reference=reference,
                metadata={
                    'user_id': request.user.id,
                    'pharmacy_id': pharmacy.id,
                    'subscription_id': subscription.id,
                    'plan_id': plan.id,
                    'payment_type': 'pharmacy_subscription'
                },
                customer_name=pharmacy.name
            )
            
            if result.get('status') == 'success':
                subscription.payment_reference = reference
                subscription.save()
                
                return Response({
                    'subscription_id': subscription.id,
                    'plan': plan.name,
                    'amount': str(plan.annual_price),
                    'payment_url': result['data']['link'],
                    'reference': reference
                }, status=status.HTTP_200_OK)
            else:
                subscription.delete() # Delete pending subscription if payment init fails
                return Response(
                    {'error': 'Failed to initialize payment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Pharmacy subscription payment error: {e}")
            subscription.delete()
            return Response(
                {'error': f'Payment initialization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ActivatePharmacySubscriptionView(APIView):
    """
    Manually activate the latest pharmacy subscription (for debugging/admin use)
    POST /api/payments/subscriptions/pharmacy/activate/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Check if user is pharmacy staff
        if not request.user.is_pharmacy_staff or not hasattr(request.user, 'works_at_pharmacy'):
            return Response(
                {'error': 'User is not associated with a pharmacy'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pharmacy = request.user.works_at_pharmacy
        
        # Get the latest subscription record for this pharmacy
        subscription = PharmacySubscriptionRecord.objects.filter(
            pharmacy=pharmacy
        ).order_by('-created_at').first()
        
        if not subscription:
            return Response(
                {'error': 'No subscription found for this pharmacy'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Activate the subscription
        subscription.status = 'active'
        subscription.save()
        
        # Update pharmacy expiry
        pharmacy.subscription_expiry = subscription.current_period_end
        pharmacy.save()
        
        return Response({
            'message': 'Subscription activated successfully',
            'pharmacy': pharmacy.name,
            'expiry_date': pharmacy.subscription_expiry,
            'subscription_id': subscription.id
        })
