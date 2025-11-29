# pharmacy/views.py
from rest_framework import generics, permissions, filters, status, views, viewsets
from rest_framework.routers import DefaultRouter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from notifications.utils import create_notification
from pharmacy.models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder, MedicationLog
from pharmacy.serializers import (
    PharmacySerializer, PharmacyOrderListSerializer,
    PharmacyOrderDetailSerializer, PharmacyOrderUpdateSerializer,
    MedicationSerializer, PharmacyInventorySerializer,
    MedicationOrderSerializer, MedicationReminderSerializer,
    MedicationLogSerializer
)
from .permissions import IsPharmacyStaffOfOrderPharmacy
from doctors.models import Prescription, PrescriptionItem, Appointment
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
import logging

logger = logging.getLogger(__name__)


class PharmacyDetailView(generics.RetrieveAPIView):
    queryset = Pharmacy.objects.all()
    serializer_class = PharmacySerializer
    permission_classes = [permissions.AllowAny]


class PharmacyListView(generics.ListAPIView):
    serializer_class = PharmacySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address']

    def get_queryset(self):
        """
        Filter pharmacies by proximity using GeoDjango if lat, lon, and radius params are provided.
        """
        queryset = Pharmacy.objects.all()

        # --- Proximity Filtering ---
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lon')
        radius_km_str = self.request.query_params.get('radius', default=5)  # Default radius 5km

        if latitude and longitude:
            try:
                lat_float = float(latitude)
                lon_float = float(longitude)
                radius_km_float = float(radius_km_str)

                if not (-90 <= lat_float <= 90 and -180 <= lon_float <= 180):
                    raise ValueError("Latitude or longitude out of valid range.")
                if not (0 < radius_km_float <= 200): # Example: Max radius 200km
                    raise ValueError("Search radius out of valid range.")

                user_location = Point(lon_float, lat_float, srid=4326) # Lon, Lat order for Point
                queryset = queryset.filter(
                    location__distance_lte=(user_location, D(km=radius_km_float))
                ).annotate(distance=Distance('location', user_location)).order_by('distance') # Optionally order by distance
                # Note: .order_by('distance') might override your default .order_by('name')
                # You might want to apply distance ordering only if location filter is active.

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid location parameters for proximity search: "
                    f"lat='{latitude}', lon='{longitude}', radius='{radius_km_str}'. Error: {e}"
                )
                # Option: Silently ignore and don't filter by location (as it currently does by falling through)
                # Option: If you want to inform the frontend, you'd typically raise an APIException
                # from rest_framework.exceptions import ParseError
                # raise ParseError("Invalid location or radius parameters provided for proximity search.")
                # For now, we'll log and proceed without location filtering if params are bad.
                pass
        # --- End Proximity Filtering ---

        # Add other filters here if needed (e.g., offers_delivery, is_24_hours)
        offers_delivery = self.request.query_params.get('offers_delivery')
        if offers_delivery is not None:
            queryset = queryset.filter(offers_delivery=str(offers_delivery).lower() in ['true', '1'])

        is_24_hours = self.request.query_params.get('is_24_hours')
        if is_24_hours is not None:
            queryset = queryset.filter(is_24_hours=str(is_24_hours).lower() in ['true', '1'])

        return queryset.order_by('name')
    
class PharmacyOrderListView(generics.ListAPIView):
    """Lists orders for the logged-in pharmacy staff's pharmacy."""
    serializer_class = PharmacyOrderListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPharmacyStaffOfOrderPharmacy]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_delivery']
    ordering_fields = ['order_date', 'status']
    ordering = ['-order_date']

    def get_queryset(self):
        """Filter orders for the staff member's assigned pharmacy."""
        user = self.request.user
        if hasattr(user, 'works_at_pharmacy') and user.works_at_pharmacy:
            return MedicationOrder.objects.filter(pharmacy=user.works_at_pharmacy)
        return MedicationOrder.objects.none()

class PharmacyOrderDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or Update a specific order for the pharmacy."""
    queryset = MedicationOrder.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsPharmacyStaffOfOrderPharmacy]

    def get_serializer_class(self):
        """Use different serializers for retrieve (GET) vs update (PATCH/PUT)."""
        if self.request.method in ['PUT', 'PATCH']:
            return PharmacyOrderUpdateSerializer
        return PharmacyOrderDetailSerializer
    
    def perform_update(self, serializer):
        """Override to trigger notification on status change by pharmacy and handle insurance."""
        old_instance = self.get_object()
        
        # Handle payment_reference if provided
        payment_reference = serializer.validated_data.pop('payment_reference', None)
        old_payment_status = old_instance.payment_status
        
        new_instance = serializer.save()
        
        # Update payment fields if payment_reference is provided
        payment_status_changed = False
        if payment_reference:
            new_instance.payment_reference = payment_reference
            new_instance.payment_status = 'paid'
            new_instance.save()
            payment_status_changed = (old_payment_status != 'paid' and new_instance.payment_status == 'paid')
        
        # Send notification when payment is confirmed
        if payment_status_changed:
            try:
                patient = new_instance.user
                create_notification(
                    recipient=patient,
                    verb=f"Payment confirmed for your medication order #{new_instance.id}.",
                    title=f"Payment Confirmed - Order #{new_instance.id}",
                    level='success',
                    category='order',
                    action_url=f"/orders/{new_instance.id}",
                    action_text="View Order"
                )
                print(f"Payment confirmation notification created for user {patient.id} for order {new_instance.id}")
            except Exception as e:
                print(f"Error creating payment confirmation notification for order {new_instance.id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Check if payment is required when trying to change status from pending
        # Payment is required when pharmacy sets total_amount and user tries to proceed
        # Only check this when status is actually being changed, not when just updating total_amount
        status_changed = old_instance.status != new_instance.status
        if status_changed and old_instance.status == 'pending' and new_instance.status != 'pending' and new_instance.status != 'cancelled':
            if not new_instance.user_insurance and new_instance.total_amount and new_instance.total_amount > 0:
                if not new_instance.payment_reference or new_instance.payment_status != 'paid':
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({
                        'status': 'Payment is required for this order. Please ensure the patient has completed payment before the order can proceed to processing.'
                    })
        
        # Check if total_amount was just added (price was set for the first time)
        total_amount_added = (
            (old_instance.total_amount is None or old_instance.total_amount == 0) and
            new_instance.total_amount and
            new_instance.total_amount > 0
        )
        
        # Send notification when pharmacy adds prices to order
        if total_amount_added:
            try:
                patient = new_instance.user
                pharmacy_name = new_instance.pharmacy.name if new_instance.pharmacy else "Pharmacy"
                
                # Format the total amount
                from decimal import Decimal
                total_formatted = f"₦{Decimal(str(new_instance.total_amount)):,.2f}"
                
                # Check if insurance is being used
                if new_instance.user_insurance:
                    message = f"Your medication order #{new_instance.id} from {pharmacy_name} has been priced at {total_formatted}. Your insurance coverage and copay have been calculated."
                else:
                    message = f"Your medication order #{new_instance.id} from {pharmacy_name} has been priced at {total_formatted}. Please proceed with payment to continue."
                
                create_notification(
                    recipient=patient,
                    verb=message,
                    title=f"Order #{new_instance.id} Priced",
                    level='info',
                    category='order',
                    action_url=f"/orders/{new_instance.id}",
                    action_text="View Order & Pay"
                )
                logger.info(f"Price notification created for user {patient.id} for order {new_instance.id} (total: {total_formatted})")
            except Exception as e:
                logger.error(f"Error creating price notification for order {new_instance.id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Recalculate insurance if total_amount is updated
        if new_instance.user_insurance and new_instance.total_amount:
            from insurance.utils import calculate_insurance_coverage
            from decimal import Decimal
            
            total_amount = Decimal(str(new_instance.total_amount))
            coverage = calculate_insurance_coverage(
                new_instance.user_insurance,
                total_amount,
                service_type='medication'
            )
            
            new_instance.insurance_covered_amount = coverage['covered_amount']
            new_instance.patient_copay = coverage['patient_copay']
            new_instance.save()
        
        # Generate insurance claim automatically when order is completed
        if old_instance.status != new_instance.status and new_instance.status == 'completed':
            if new_instance.user_insurance and new_instance.total_amount and not new_instance.insurance_claim_generated:
                from insurance.utils import generate_insurance_claim
                from django.utils import timezone
                
                try:
                    # Build service description from order items
                    items_desc = ", ".join([
                        f"{item.medication_name_text or 'Medication'} ({item.quantity}x)"
                        for item in new_instance.items.all()
                    ])
                    
                    claim = generate_insurance_claim(
                        user_insurance=new_instance.user_insurance,
                        service_type='medication',
                        service_date=new_instance.order_date.date(),
                        provider_name=new_instance.pharmacy.name,
                        service_description=f"Medication Order: {items_desc}",
                        claimed_amount=new_instance.total_amount,
                        approved_amount=new_instance.insurance_covered_amount,
                        patient_responsibility=new_instance.patient_copay,
                    )
                    new_instance.insurance_claim_generated = True
                    new_instance.save()
                except Exception as e:
                    print(f"Error generating insurance claim for order {new_instance.id}: {e}")

        # Send notifications for order status changes
        status_changed = old_instance.status != new_instance.status
        if status_changed:
            try:
                patient = new_instance.user
                pharmacy_name = new_instance.pharmacy.name if new_instance.pharmacy else "Pharmacy"
                
                if new_instance.status == 'processing':
                    create_notification(
                        recipient=patient,
                        verb=f"Your medication order #{new_instance.id} from {pharmacy_name} is now being processed.",
                        title=f"Order #{new_instance.id} Processing",
                        level='info',
                        category='order',
                        action_url=f"/orders/{new_instance.id}",
                        action_text="View Order"
                    )
                elif new_instance.status == 'ready':
                    delivery_text = 'delivery' if new_instance.is_delivery else 'pickup'
                    create_notification(
                        recipient=patient,
                        verb=f"Your medication order #{new_instance.id} from {pharmacy_name} is ready for {delivery_text}.",
                        title=f"Order #{new_instance.id} Ready",
                        level='success',
                        category='order',
                        action_url=f"/orders/{new_instance.id}",
                        action_text="View Order"
                    )
                elif new_instance.status == 'delivering':
                    create_notification(
                        recipient=patient,
                        verb=f"Your medication order #{new_instance.id} from {pharmacy_name} is out for delivery.",
                        title=f"Order #{new_instance.id} Out for Delivery",
                        level='info',
                        category='order',
                        action_url=f"/orders/{new_instance.id}",
                        action_text="Track Order"
                    )
                elif new_instance.status == 'completed':
                    create_notification(
                        recipient=patient,
                        verb=f"Your medication order #{new_instance.id} from {pharmacy_name} has been completed.",
                        title=f"Order #{new_instance.id} Completed",
                        level='success',
                        category='order',
                        action_url=f"/orders/{new_instance.id}",
                        action_text="View Order"
                    )
                elif new_instance.status == 'cancelled':
                    create_notification(
                        recipient=patient,
                        verb=f"Your medication order #{new_instance.id} from {pharmacy_name} has been cancelled.",
                        title=f"Order #{new_instance.id} Cancelled",
                        level='warning',
                        category='order',
                        action_url=f"/orders/{new_instance.id}",
                        action_text="View Details"
                    )
                
                print(f"Status change notification created for user {patient.id} for order {new_instance.id} (status: {new_instance.status})")
            except Exception as e:
                print(f"Error creating status change notification for order {new_instance.id}: {e}")
                import traceback
                traceback.print_exc()

class MedicationListView(generics.ListAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'generic_name']

class PharmacyInventoryListView(generics.ListAPIView):
    serializer_class = PharmacyInventorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return PharmacyInventory.objects.filter(pharmacy_id=self.kwargs['pharmacy_id'], in_stock=True)


class PharmacyInventoryPortalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for pharmacy staff to manage their own pharmacy's inventory.
    Only allows pharmacy staff to view/edit inventory for their assigned pharmacy.
    """
    serializer_class = PharmacyInventorySerializer
    permission_classes = [permissions.IsAuthenticated, IsPharmacyStaffOfOrderPharmacy]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['medication__name', 'medication__generic_name']
    filterset_fields = ['in_stock']

    def get_queryset(self):
        """Only return inventory for the authenticated pharmacy staff's pharmacy"""
        user = self.request.user
        if hasattr(user, 'works_at_pharmacy') and user.works_at_pharmacy:
            return PharmacyInventory.objects.filter(pharmacy=user.works_at_pharmacy)
        return PharmacyInventory.objects.none()

    def perform_create(self, serializer):
        """Automatically set the pharmacy to the authenticated user's pharmacy"""
        user = self.request.user
        if hasattr(user, 'works_at_pharmacy') and user.works_at_pharmacy:
            serializer.save(pharmacy=user.works_at_pharmacy)
        else:
            raise permissions.PermissionDenied("You must be assigned to a pharmacy to manage inventory.")

class CreateOrderFromPrescriptionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, prescription_id, *args, **kwargs):
        # Fetch Prescription
        prescription = get_object_or_404(Prescription, pk=prescription_id)

        # --- Validation 1: Check Prescription Ownership ---
        if prescription.user != request.user:
            return Response(
                {"error": "You do not have permission to order from this prescription."},
                status=status.HTTP_403_FORBIDDEN
            )

        # --- Validation 2: Check Related Appointment Status ---
        try:
            # Ensure the related appointment exists and is completed
            if not prescription.appointment:
                 # Should ideally not happen due to model constraints, but good to check
                 return Response(
                    {"error": "Prescription is not linked to a valid appointment."},
                    status=status.HTTP_400_BAD_REQUEST
                 )
            if prescription.appointment.status != Appointment.StatusChoices.COMPLETED:
                 return Response(
                     {"error": f"Cannot create order: The associated appointment (ID: {prescription.appointment.id}) is not marked as 'Completed'. Current status: '{prescription.appointment.get_status_display()}'."},
                     status=status.HTTP_400_BAD_REQUEST
                 )
        except AttributeError:
             # Handle case where appointment relationship might be broken unexpectedly
             return Response(
                {"error": "Error accessing associated appointment details."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
             )
        # --- End Validation 2 ---


        # Fetch Pharmacy ID and Insurance from request body
        pharmacy_id = request.data.get('pharmacy_id')
        if not pharmacy_id:
            return Response(
                {"error": "pharmacy_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle Insurance if provided
        user_insurance = None
        user_insurance_id = request.data.get('user_insurance_id')
        if user_insurance_id:
            from insurance.models import UserInsurance
            try:
                user_insurance = UserInsurance.objects.get(id=user_insurance_id, user=request.user)
            except UserInsurance.DoesNotExist:
                pass  # Continue without insurance if invalid

        # Fetch Pharmacy
        try:
            pharmacy = Pharmacy.objects.get(pk=pharmacy_id)
        except Pharmacy.DoesNotExist:
            return Response(
                {"error": f"Pharmacy with ID {pharmacy_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, TypeError):
             return Response(
                {"error": f"Invalid pharmacy_id format provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Validation 3: Check if Pharmacy is Active ---
        if not pharmacy.is_active:
            return Response(
                {"error": f"The selected pharmacy '{pharmacy.name}' is currently inactive and cannot accept orders."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # --- End Validation 3 ---


        # --- Validation 4: Check if Order Already Exists ---
        # MODIFIED: Return 409 Conflict instead of 200 OK with warning
        existing_order = MedicationOrder.objects.filter(prescription=prescription).first()
        if existing_order:
            # Serialize existing order to optionally return some info if needed
            # serializer = MedicationOrderSerializer(existing_order)
            return Response(
                {
                    "error": "An order for this prescription already exists.",
                    "existing_order_id": existing_order.id,
                    "existing_order_status": existing_order.status,
                 },
                status=status.HTTP_409_CONFLICT # Use 409 Conflict
            )
        # --- End Validation 4 ---


        # --- Validation 5: Check if Prescription Has Items ---
        prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
        if not prescription_items.exists():
            return Response(
                {"error": "Prescription has no items to order."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # --- End Validation 5 ---


        # --- Handle Insurance if provided ---
        user_insurance = None
        user_insurance_id = request.data.get('user_insurance_id')
        if user_insurance_id:
            from insurance.models import UserInsurance
            try:
                user_insurance = UserInsurance.objects.get(id=user_insurance_id, user=request.user)
            except UserInsurance.DoesNotExist:
                pass  # Continue without insurance if invalid
        
        # --- Handle Payment if no insurance ---
        payment_reference = request.data.get('payment_reference', None)
        
        # If no insurance, payment is required (will be set when pharmacy sets total_amount)
        # For now, we'll create the order and payment will be required when pharmacy updates with total_amount
        payment_status = 'pending'
        if payment_reference:
            payment_status = 'paid'
        
        # --- Create Order and Items (If all validations pass) ---
        order = MedicationOrder.objects.create(
            user=request.user,
            pharmacy=pharmacy,
            prescription=prescription,
            status='pending', # Default status for new orders
            user_insurance=user_insurance,
            payment_reference=payment_reference,
            payment_status=payment_status,
            # is_delivery, delivery_address, total_amount, notes would be set later by user/pharmacy
        )

        # Create order items one by one to ensure IDs are set (bulk_create doesn't return IDs on all databases)
        for p_item in prescription_items:
            MedicationOrderItem.objects.create(
                order=order,
                prescription_item=p_item,
                medication_name_text=p_item.medication_name,
                dosage_text=p_item.dosage,
                quantity=1, # Default quantity, pharmacy might adjust
                # price_per_unit will be filled by pharmacy later
            )

        # Refresh the order from database to ensure items are accessible
        order.refresh_from_db()
        
        # Prefetch related items for serialization
        order = MedicationOrder.objects.prefetch_related('items__prescription_item').get(pk=order.pk)

        # Send notifications to all pharmacy staff members
        try:
            from users.models import User
            pharmacy_staff = User.objects.filter(
                is_pharmacy_staff=True,
                works_at_pharmacy=pharmacy,
                is_active=True
            )
            
            patient_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
            prescription_items_count = prescription_items.count()
            
            for staff_member in pharmacy_staff:
                create_notification(
                    recipient=staff_member,
                    verb=f"New medication order #{order.id} received from {patient_name}. Prescription includes {prescription_items_count} medication(s).",
                    title=f"New Order #{order.id}",
                    level='info',
                    category='order',
                    actor=request.user,
                    action_url=f"/portal/orders/{order.id}",
                    action_text="View Order"
                )
            logger.info(f"Created notifications for {pharmacy_staff.count()} pharmacy staff members for order {order.id}")
        except Exception as e:
            logger.error(f"Error creating notifications for pharmacy staff for order {order.id}: {e}")
            import traceback
            traceback.print_exc()

        # Serialize the newly created order
        try:
            serializer = MedicationOrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error serializing order {order.id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Order created successfully but failed to serialize: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MedicationOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationOrder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Handle insurance if provided
        user_insurance_id = serializer.validated_data.pop('user_insurance_id', None)
        user_insurance = None
        if user_insurance_id:
            from insurance.models import UserInsurance
            try:
                user_insurance = UserInsurance.objects.get(id=user_insurance_id, user=self.request.user)
            except UserInsurance.DoesNotExist:
                pass  # Continue without insurance if invalid
        
        order = serializer.save(user=self.request.user, user_insurance=user_insurance)
        
        # Send notifications to all pharmacy staff members
        if order.pharmacy:
            try:
                from users.models import User
                pharmacy_staff = User.objects.filter(
                    is_pharmacy_staff=True,
                    works_at_pharmacy=order.pharmacy,
                    is_active=True
                )
                
                patient_name = f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.email
                items_count = order.items.count() if hasattr(order, 'items') else 0
                
                for staff_member in pharmacy_staff:
                    create_notification(
                        recipient=staff_member,
                        verb=f"New medication order #{order.id} received from {patient_name}. Order includes {items_count} medication(s).",
                        title=f"New Order #{order.id}",
                        level='info',
                        category='order',
                        actor=self.request.user,
                        action_url=f"/portal/orders/{order.id}",
                        action_text="View Order"
                    )
                logger.info(f"Created notifications for {pharmacy_staff.count()} pharmacy staff members for order {order.id}")
            except Exception as e:
                logger.error(f"Error creating notifications for pharmacy staff for order {order.id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Calculate insurance coverage if insurance is selected and total_amount is set
        if user_insurance and order.total_amount:
            from insurance.utils import calculate_insurance_coverage
            from decimal import Decimal
            
            total_amount = Decimal(str(order.total_amount))
            coverage = calculate_insurance_coverage(
                user_insurance,
                total_amount,
                service_type='medication'
            )
            
            order.insurance_covered_amount = coverage['covered_amount']
            order.patient_copay = coverage['patient_copay']
            order.save()

class MedicationOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationOrder.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Override update to ensure we return the updated instance with correct payment_status"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Get the updated instance (it should have payment_status updated in perform_update)
        updated_instance = self.get_object()
        # Force refresh from database to ensure we have the latest payment_status
        updated_instance.refresh_from_db(fields=['payment_reference', 'payment_status', 'status', 'total_amount'])
        
        # Return the updated instance with fresh data
        response_serializer = self.get_serializer(updated_instance)
        response_data = response_serializer.data
        
        # Ensure payment_status is in the response (in case serializer method fails)
        # Force refresh payment_status from database to ensure we return the latest value
        updated_instance.refresh_from_db(fields=['payment_status', 'payment_reference'])
        actual_payment_status = updated_instance.payment_status
        
        # Override payment_status in response if serializer method didn't return correct value
        if 'payment_status' not in response_data or response_data['payment_status'] != actual_payment_status:
            logger.warning(f"Payment status mismatch - serializer returned: {response_data.get('payment_status')}, actual DB value: {actual_payment_status}")
            response_data['payment_status'] = actual_payment_status
        
        # Also ensure payment_reference is in response if it exists
        if updated_instance.payment_reference and 'payment_reference' not in response_data:
            response_data['payment_reference'] = updated_instance.payment_reference
        
        logger.info(f"Returning order {updated_instance.id} with payment_status: {response_data.get('payment_status')}, payment_reference: {response_data.get('payment_reference')}")
        return Response(response_data)
    
    def perform_update(self, serializer):
        """Override to handle insurance calculation and claim generation."""
        old_instance = self.get_object()
        
        # Handle insurance if being updated
        user_insurance_id = serializer.validated_data.pop('user_insurance_id', None)
        payment_reference = serializer.validated_data.pop('payment_reference', None)
        user_insurance = old_instance.user_insurance  # Keep existing if not updating
        
        if user_insurance_id is not None:  # Explicitly set (could be None to remove)
            from insurance.models import UserInsurance
            if user_insurance_id:
                try:
                    user_insurance = UserInsurance.objects.get(id=user_insurance_id, user=self.request.user)
                except UserInsurance.DoesNotExist:
                    pass  # Keep existing insurance if invalid
            else:
                user_insurance = None  # Remove insurance
        
        new_instance = serializer.save(user_insurance=user_insurance)
        
        # Update payment fields if payment_reference is provided
        payment_status_changed = False
        if payment_reference:
            old_payment_status = old_instance.payment_status
            logger.info(f"Updating order {new_instance.id} with payment_reference: {payment_reference}")
            logger.info(f"Order {new_instance.id} current payment_status before update: {new_instance.payment_status}")
            logger.info(f"Order {new_instance.id} current payment_reference before update: {new_instance.payment_reference}")
            
            # Use update() to ensure atomic update
            from pharmacy.models import MedicationOrder
            updated_count = MedicationOrder.objects.filter(pk=new_instance.id).update(
                payment_reference=payment_reference,
                payment_status='paid'
            )
            
            if updated_count > 0:
                logger.info(f"✓ Order {new_instance.id} payment fields updated successfully via QuerySet.update()")
                # Refresh the instance to get updated values
                new_instance.refresh_from_db(fields=['payment_reference', 'payment_status'])
                logger.info(f"Order {new_instance.id} payment_status after refresh: {new_instance.payment_status}")
                logger.info(f"Order {new_instance.id} payment_reference after refresh: {new_instance.payment_reference}")
                payment_status_changed = (old_payment_status != 'paid' and new_instance.payment_status == 'paid')
            else:
                logger.error(f"❌ Failed to update order {new_instance.id} - no rows affected")
        
        # Send notification when payment is confirmed
        if payment_status_changed:
            try:
                patient = new_instance.user
                create_notification(
                    recipient=patient,
                    verb=f"Payment confirmed for your medication order #{new_instance.id}.",
                    title=f"Payment Confirmed - Order #{new_instance.id}",
                    level='success',
                    category='order',
                    action_url=f"/orders/{new_instance.id}",
                    action_text="View Order"
                )
                logger.info(f"Payment confirmation notification created for user {patient.id} for order {new_instance.id}")
            except Exception as e:
                logger.error(f"Error creating payment confirmation notification for order {new_instance.id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Recalculate insurance if total_amount is set and insurance exists
        if user_insurance and new_instance.total_amount:
            from insurance.utils import calculate_insurance_coverage
            from decimal import Decimal
            
            total_amount = Decimal(str(new_instance.total_amount))
            coverage = calculate_insurance_coverage(
                user_insurance,
                total_amount,
                service_type='medication'
            )
            
            new_instance.insurance_covered_amount = coverage['covered_amount']
            new_instance.patient_copay = coverage['patient_copay']
            new_instance.save()
        
        # Generate insurance claim automatically when order is completed
        if old_instance.status != new_instance.status and new_instance.status == 'completed':
            if new_instance.user_insurance and new_instance.total_amount and not new_instance.insurance_claim_generated:
                from insurance.utils import generate_insurance_claim
                from django.utils import timezone
                
                try:
                    # Build service description from order items
                    items_desc = ", ".join([
                        f"{item.medication_name_text or 'Medication'} ({item.quantity}x)"
                        for item in new_instance.items.all()
                    ])
                    
                    claim = generate_insurance_claim(
                        user_insurance=new_instance.user_insurance,
                        service_type='medication',
                        service_date=new_instance.order_date.date(),
                        provider_name=new_instance.pharmacy.name,
                        service_description=f"Medication Order: {items_desc}",
                        claimed_amount=new_instance.total_amount,
                        approved_amount=new_instance.insurance_covered_amount,
                        patient_responsibility=new_instance.patient_copay,
                    )
                    new_instance.insurance_claim_generated = True
                    new_instance.save()
                except Exception as e:
                    print(f"Error generating insurance claim for order {new_instance.id}: {e}")

class MedicationReminderListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationReminder.objects.filter(user=self.request.user).select_related('medication')

    def perform_create(self, serializer):
        medication_name = self.request.data.get('medication_name')
        medication_instance = None
        if medication_name:
            medication_instance, _ = Medication.objects.get_or_create(
                name__iexact=medication_name,
                defaults={
                    'description': 'Medication details to be updated.',
                    'dosage_form': 'Unknown',
                    'strength': 'N/A',
                }
            )
        if medication_instance:
            serializer.save(user=self.request.user, medication=medication_instance)
        else:
            raise ValidationError({'medication_name': 'A valid medication is required.'})
            serializer.save(user=self.request.user)


class MedicationReminderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationReminder.objects.filter(user=self.request.user).select_related('medication')

    def perform_update(self, serializer):
        medication_name = self.request.data.get('medication_name')
        medication_instance = None
        
        if medication_name:
            medication_instance, _ = Medication.objects.get_or_create(
                name__iexact=medication_name,
                defaults={
                    'description': 'Medication details to be updated.',
                    'dosage_form': 'Unknown',
                    'strength': 'N/A',
                }
            )
        
        if medication_instance:
            serializer.save(medication=medication_instance)
        else:
            serializer.save()

class MedicationLogListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reminder']
    ordering_fields = ['scheduled_time', 'taken_at']
    ordering = ['-scheduled_time']

    def get_queryset(self):
        # Filter logs for reminders belonging to the current user
        return MedicationLog.objects.filter(reminder__user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the reminder belongs to the user
        reminder = serializer.validated_data['reminder']
        if reminder.user != self.request.user:
            raise ValidationError("You cannot log intake for another user's reminder.")
        serializer.save()

class LogMedicationIntakeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, reminder_id):
        reminder = get_object_or_404(MedicationReminder, pk=reminder_id, user=request.user)
        
        status_value = request.data.get('status', 'taken')
        taken_at = request.data.get('taken_at') # Optional override
        notes = request.data.get('notes', '')
        
        if not taken_at and status_value == 'taken':
            from django.utils import timezone
            taken_at = timezone.now()
            
        # Create the log entry
        log = MedicationLog.objects.create(
            reminder=reminder,
            scheduled_time=taken_at or timezone.now(), # Simplified logic; ideally match to next schedule
            taken_at=taken_at,
            status=status_value,
            notes=notes
        )
        
        return Response(MedicationLogSerializer(log).data, status=status.HTTP_201_CREATED)
        taken_at = request.data.get('taken_at') # Optional override
        notes = request.data.get('notes', '')
        
        if not taken_at and status_value == 'taken':
            from django.utils import timezone
            taken_at = timezone.now()
            
        # Create the log entry
        log = MedicationLog.objects.create(
            reminder=reminder,
            scheduled_time=taken_at or timezone.now(), # Simplified logic; ideally match to next schedule
            taken_at=taken_at,
            status=status_value,
            notes=notes
        )
        
        return Response(MedicationLogSerializer(log).data, status=status.HTTP_201_CREATED)