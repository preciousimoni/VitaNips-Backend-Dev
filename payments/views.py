# payments/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.conf import settings
from .services import flutterwave_service
import uuid
import logging

logger = logging.getLogger(__name__)

class InitializePaymentView(APIView):
    """
    Initialize a payment transaction
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Initialize payment for appointment or medication order
        
        Expected payload:
        {
            "amount": 5000.00,
            "email": "user@example.com",
            "payment_type": "appointment" | "medication_order",
            "payment_for_id": 123,  # appointment_id or order_id
            "callback_url": "https://..." (optional)
        }
        """
        amount = request.data.get('amount')
        email = request.data.get('email') or request.user.email
        payment_type = request.data.get('payment_type')  # 'appointment' or 'medication_order'
        payment_for_id = request.data.get('payment_for_id')
        callback_url = request.data.get('callback_url')
        
        # Validation
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if amount <= 0:
            return Response(
                {'error': 'Amount must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not payment_type or payment_type not in ['appointment', 'medication_order']:
            return Response(
                {'error': 'Invalid payment_type. Must be "appointment" or "medication_order"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique reference
        reference = f"{payment_type}_{payment_for_id}_{uuid.uuid4().hex[:10]}"
        
        # Metadata for tracking
        metadata = {
            'user_id': request.user.id,
            'payment_type': payment_type,
            'payment_for_id': payment_for_id,
            'user_email': email
        }
        
        try:
            # Get customer name if available
            customer_name = None
            if hasattr(request.user, 'first_name') and hasattr(request.user, 'last_name'):
                customer_name = f"{request.user.first_name} {request.user.last_name}".strip()
            
            # Initialize payment with Flutterwave
            result = flutterwave_service.initialize_transaction(
                email=email,
                amount=amount,
                reference=reference,
                callback_url=callback_url,
                metadata=metadata,
                customer_name=customer_name
            )
            
            if result.get('status') == 'success':
                return Response({
                    'authorization_url': result['data']['link'],
                    'reference': reference,
                    'tx_ref': result['data'].get('tx_ref', reference),
                    'amount': str(amount),
                    'public_key': getattr(settings, 'FLUTTERWAVE_PUBLIC_KEY', '')
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': result.get('message', 'Failed to initialize payment')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Payment initialization error: {e}")
            return Response(
                {'error': f'Payment initialization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentView(APIView):
    """
    Verify a payment transaction
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Verify payment after user completes payment
        
        Expected payload:
        {
            "reference": "appointment_123_abc123"
        }
        """
        reference = request.data.get('reference')
        
        if not reference:
            return Response(
                {'error': 'Payment reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify payment with Flutterwave
            # Flutterwave verify endpoint uses transaction ID, but we might receive tx_ref
            # Try the reference first, and if it fails, we'll handle it
            result = flutterwave_service.verify_transaction(reference)
            
            if result.get('status') == 'success' and result['data'].get('status') == 'successful':
                # Extract metadata - Flutterwave returns it in 'meta' field
                transaction_data = result.get('data', {})
                metadata = transaction_data.get('meta', {})
                
                # If metadata is empty, try to extract from the reference pattern
                # Our reference format is: {payment_type}_{payment_for_id}_{uuid}
                if not metadata or not metadata.get('payment_type'):
                    import re
                    ref_match = re.match(r'^(\w+)_(\d+)_', reference)
                    if ref_match:
                        metadata = {
                            'payment_type': ref_match.group(1),
                            'payment_for_id': int(ref_match.group(2)),
                            'user_id': request.user.id
                        }
                
                return Response({
                    'verified': True,
                    'reference': reference,
                    'tx_ref': transaction_data.get('tx_ref', reference),
                    'transaction_id': transaction_data.get('id'),
                    'amount': transaction_data.get('amount', 0),
                    'paid_at': transaction_data.get('created_at'),
                    'customer': transaction_data.get('customer', {}),
                    'metadata': metadata
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'verified': False,
                    'message': result.get('message', 'Payment verification failed')
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return Response(
                {'error': f'Payment verification failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentWebhookView(APIView):
    """
    Handle Flutterwave webhook for payment events
    """
    permission_classes = []  # No auth required for webhooks
    authentication_classes = []  # Flutterwave will send webhook
    
    def post(self, request):
        """
        Handle Flutterwave webhook events
        """
        # Verify webhook signature (implement Flutterwave signature verification)
        # Flutterwave sends a 'verif_hash' header for verification
        # For now, we'll process the webhook
        
        event = request.data.get('event')
        data = request.data.get('data', {})
        
        if event == 'charge.completed':
            reference = data.get('tx_ref')
            status_value = data.get('status')
            
            if status_value == 'successful':
                # Update payment status in database
                # This will be handled by the respective models (Appointment/MedicationOrder)
                logger.info(f"Payment successful for reference: {reference}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Payment failed for reference: {reference}, status: {status_value}")
        
        return Response({'status': 'received'}, status=status.HTTP_200_OK)

