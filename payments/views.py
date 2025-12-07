# payments/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .services import flutterwave_service
from .commission_service import (
    calculate_appointment_commission,
    calculate_medication_order_commission,
    calculate_virtual_session_commission,
    get_commission_breakdown
)
from .models import Transaction
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
        
        if not payment_type or payment_type not in ['appointment', 'medication_order', 'virtual_session']:
            return Response(
                {'error': 'Invalid payment_type. Must be "appointment", "medication_order", or "virtual_session"'},
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
            
            # Check for split payment
            subaccount_id = None
            commission_rate = None
            
            if payment_type == 'appointment':
                from doctors.models import Appointment
                try:
                    appointment = Appointment.objects.get(id=payment_for_id)
                    if appointment.doctor and appointment.doctor.subaccount_id:
                        subaccount_id = appointment.doctor.subaccount_id
                        commission_rate = appointment.doctor.commission_rate
                except Appointment.DoesNotExist:
                    pass
            elif payment_type == 'medication_order':
                from pharmacy.models import MedicationOrder
                try:
                    order = MedicationOrder.objects.get(id=payment_for_id)
                    if order.pharmacy and order.pharmacy.subaccount_id:
                        subaccount_id = order.pharmacy.subaccount_id
                        commission_rate = order.pharmacy.commission_rate
                except MedicationOrder.DoesNotExist:
                    pass
            
            if subaccount_id:
                # Use split payment
                from .utils import initiate_split_payment
                
                # Calculate split
                # Platform commission is taken from the total amount
                # If commission_rate is 10%, platform takes 10%, provider gets 90%
                # Flutterwave split logic: transaction_charge is platform fee?
                # initiate_split_payment handles the logic
                
                result = initiate_split_payment(
                    email=email,
                    amount=float(amount),
                    reference=reference,
                    subaccount_id=subaccount_id,
                    commission_percentage=float(commission_rate) if commission_rate else 10.0, # Default 10%
                    callback_url=callback_url,
                    metadata=metadata,
                    customer_name=customer_name
                )
            else:
                # Standard payment (platform takes all)
                result = flutterwave_service.initialize_transaction(
                    email=email,
                    amount=amount,
                    reference=reference,
                    callback_url=callback_url,
                    metadata=metadata,
                    customer_name=customer_name
                )
            
            if result.get('status') == 'success':
                # Calculate commission breakdown for display
                commission_breakdown = get_commission_breakdown(payment_type, amount)
                
                return Response({
                    'authorization_url': result['data']['link'],
                    'reference': reference,
                    'tx_ref': result['data'].get('tx_ref', reference),
                    'amount': str(amount),
                    'public_key': getattr(settings, 'FLUTTERWAVE_PUBLIC_KEY', ''),
                    'commission_breakdown': commission_breakdown
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
                
                # Get payment details
                payment_type = metadata.get('payment_type', 'unknown')
                payment_for_id = metadata.get('payment_for_id')
                gross_amount = Decimal(str(transaction_data.get('amount', 0)))
                
                # Calculate commission
                # Calculate commission
                commission_rate = None
                
                if payment_type == 'appointment':
                    from doctors.models import Appointment
                    try:
                        appointment = Appointment.objects.get(id=payment_for_id)
                        if appointment.doctor:
                            commission_rate = appointment.doctor.commission_rate
                    except Appointment.DoesNotExist:
                        pass
                    
                    if commission_rate is not None:
                        commission = gross_amount * (commission_rate / Decimal('100.0'))
                        net_amount = gross_amount - commission
                    else:
                        commission, net_amount = calculate_appointment_commission(gross_amount)
                        
                elif payment_type == 'medication_order':
                    from pharmacy.models import MedicationOrder
                    try:
                        order = MedicationOrder.objects.get(id=payment_for_id)
                        if order.pharmacy:
                            commission_rate = order.pharmacy.commission_rate
                    except MedicationOrder.DoesNotExist:
                        pass
                        
                    if commission_rate is not None:
                        commission = gross_amount * (commission_rate / Decimal('100.0'))
                        net_amount = gross_amount - commission
                    else:
                        commission, net_amount = calculate_medication_order_commission(gross_amount)
                elif payment_type == 'virtual_session':
                    commission, net_amount = calculate_virtual_session_commission(gross_amount, use_flat_fee=True)
                else:
                    commission = Decimal('0.00')
                    net_amount = gross_amount
                
                # Create transaction record
                transaction = Transaction.objects.create(
                    transaction_type=payment_type,
                    reference=reference,
                    user=request.user,
                    related_object_id=payment_for_id,
                    related_object_type=payment_type,
                    gross_amount=gross_amount,
                    platform_commission=commission,
                    net_amount=net_amount,
                    status='completed',
                    payment_gateway='flutterwave',
                    payment_method=transaction_data.get('payment_type', 'unknown'),
                    completed_at=timezone.now()
                )
                
                # Update the related object's payment status
                # This will be handled by signals or the respective views
                _update_payment_status(payment_type, payment_for_id, reference, 'paid')
                
                return Response({
                    'verified': True,
                    'reference': reference,
                    'tx_ref': transaction_data.get('tx_ref', reference),
                    'transaction_id': transaction.transaction_id,
                    'amount': str(gross_amount),
                    'platform_commission': str(commission),
                    'net_amount': str(net_amount),
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


def _update_payment_status(payment_type: str, payment_for_id: int, reference: str, status: str):
    """
    Helper function to update payment status on related objects
    """
    try:
        if payment_type == 'appointment':
            from doctors.models import Appointment
            appointment = Appointment.objects.get(id=payment_for_id)
            appointment.payment_reference = reference
            appointment.payment_status = status
            appointment.save()
        elif payment_type == 'medication_order':
            from pharmacy.models import MedicationOrder
            order = MedicationOrder.objects.get(id=payment_for_id)
            order.payment_reference = reference
            order.payment_status = status
            order.save()
        elif payment_type == 'virtual_session':
            # Virtual sessions are linked to appointments
            from doctors.models import Appointment, VirtualSession
            try:
                appointment = Appointment.objects.get(id=payment_for_id)
                if hasattr(appointment, 'virtual_session'):
                    # Update virtual session if exists
                    pass
            except Appointment.DoesNotExist:
                pass
        elif payment_type == 'pharmacy_subscription':
            from payments.models import PharmacySubscriptionRecord
            try:
                # payment_for_id is subscription_id
                subscription = PharmacySubscriptionRecord.objects.get(id=payment_for_id)
                subscription.payment_reference = reference
                
                if status == 'paid':
                    subscription.status = 'active'
                    subscription.save()
                    
                    # Update pharmacy expiry
                    pharmacy = subscription.pharmacy
                    pharmacy.subscription_expiry = subscription.current_period_end
                    pharmacy.save()
                else:
                    subscription.status = 'cancelled' # Or failed
                    subscription.save()
            except PharmacySubscriptionRecord.DoesNotExist:
                pass
    except Exception as e:
        logger.error(f"Error updating payment status for {payment_type} {payment_for_id}: {e}")

