# payments/premium_feature_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .premium_features import (
    list_all_premium_features,
    get_premium_feature_info,
    get_premium_feature_price,
    is_premium_feature_free_for_subscription
)
from .utils import user_has_premium, get_user_subscription_tier
from .services import flutterwave_service
from .models import Transaction
from .commission_service import calculate_commission
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class PremiumFeaturesListView(APIView):
    """List all available premium features with pricing"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        features = list_all_premium_features()
        subscription_tier = get_user_subscription_tier(request.user)
        
        # Add whether each feature is free for user's subscription
        for key, feature in features.items():
            feature['is_free'] = is_premium_feature_free_for_subscription(key, subscription_tier)
            feature['price'] = str(get_premium_feature_price(key))
        
        return Response({
            'features': features,
            'user_subscription_tier': subscription_tier,
            'has_premium': user_has_premium(request.user)
        })


class PurchasePremiumFeatureView(APIView):
    """Purchase a premium feature (one-time payment)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Purchase a premium feature
        
        Expected payload:
        {
            "feature_key": "health_report" | "priority_booking" | "extended_consultation",
            "related_object_id": 123  # Optional: ID of related object (appointment, etc.)
        }
        """
        feature_key = request.data.get('feature_key')
        related_object_id = request.data.get('related_object_id')
        
        if not feature_key:
            return Response(
                {'error': 'feature_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get feature info
        feature_info = get_premium_feature_info(feature_key)
        if not feature_info:
            return Response(
                {'error': 'Invalid feature key'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if feature is free for user's subscription
        subscription_tier = get_user_subscription_tier(request.user)
        if is_premium_feature_free_for_subscription(feature_key, subscription_tier):
            return Response({
                'message': f'{feature_info["name"]} is free for your subscription tier',
                'is_free': True,
                'feature_key': feature_key
            }, status=status.HTTP_200_OK)
        
        # Get price
        amount = get_premium_feature_price(feature_key)
        
        # Generate reference
        reference = f"premium_{feature_key}_{related_object_id or 'none'}_{uuid.uuid4().hex[:10]}"
        
        # Initialize payment
        try:
            result = flutterwave_service.initialize_transaction(
                email=request.user.email,
                amount=amount,
                reference=reference,
                metadata={
                    'user_id': request.user.id,
                    'feature_key': feature_key,
                    'related_object_id': related_object_id,
                    'payment_type': 'premium_feature'
                }
            )
            
            if result.get('status') == 'success':
                return Response({
                    'feature': feature_info['name'],
                    'amount': str(amount),
                    'payment_url': result['data']['link'],
                    'reference': reference
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Failed to initialize payment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Premium feature payment error: {e}")
            return Response(
                {'error': f'Payment initialization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscribePremiumSOSView(APIView):
    """Subscribe to Premium SOS features (recurring monthly)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Subscribe to Premium SOS features
        
        Expected payload:
        {
            "action": "subscribe" | "cancel"
        }
        """
        action = request.data.get('action', 'subscribe')
        amount = get_premium_feature_price('premium_sos')
        
        if action == 'subscribe':
            # Initialize monthly subscription payment
            reference = f"premium_sos_{request.user.id}_{uuid.uuid4().hex[:10]}"
            
            try:
                result = flutterwave_service.initialize_transaction(
                    email=request.user.email,
                    amount=amount,
                    reference=reference,
                    metadata={
                        'user_id': request.user.id,
                        'feature_key': 'premium_sos',
                        'payment_type': 'premium_sos_subscription'
                    }
                )
                
                if result.get('status') == 'success':
                    # TODO: Create subscription record
                    return Response({
                        'message': 'Premium SOS subscription initiated',
                        'amount': str(amount),
                        'payment_url': result['data']['link'],
                        'reference': reference
                    }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Premium SOS subscription error: {e}")
                return Response(
                    {'error': f'Subscription failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        elif action == 'cancel':
            # TODO: Cancel subscription
            return Response({
                'message': 'Premium SOS subscription cancelled'
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )

