# payments/subscription_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import SubscriptionPlan, UserSubscription, DoctorSubscription, DoctorSubscriptionRecord
from .services import flutterwave_service
from .commission_service import get_commission_breakdown
import logging

logger = logging.getLogger(__name__)


class SubscriptionPlanListView(ListAPIView):
    """List all available subscription plans"""
    permission_classes = [IsAuthenticated]
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
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if subscription and subscription.is_active:
            return Response({
                'has_premium': True,
                'plan': subscription.plan.tier,
                'plan_name': subscription.plan.name,
                'expires_at': subscription.current_period_end
            })
        else:
            return Response({
                'has_premium': False,
                'plan': 'free'
            })

