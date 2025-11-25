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
        """Override to trigger notification on status change by pharmacy."""
        old_instance = self.get_object()
        new_instance = serializer.save()

        if old_instance.status != new_instance.status and new_instance.status == 'ready':
            patient = new_instance.user
            create_notification(
                recipient=patient,
                actor=self.request.user,
                verb=f"Your medication order #{new_instance.id} from {new_instance.pharmacy.name} is ready for {'delivery' if new_instance.is_delivery else 'pickup'}.",
                level='order',
                target_url=f"/orders/{new_instance.id}"
            )
            print(f"Order ready notification created for user {patient.id} for order {new_instance.id}")

        elif old_instance.status != new_instance.status and new_instance.status == 'delivering':
            patient = new_instance.user
            create_notification(
                recipient=patient,
                actor=self.request.user,
                verb=f"Your medication order #{new_instance.id} from {new_instance.pharmacy.name} is out for delivery.",
                level='order',
                target_url=f"/orders/{new_instance.id}"
            )
            print(f"Order delivering notification created for user {patient.id} for order {new_instance.id}")

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


        # Fetch Pharmacy ID from request body
        pharmacy_id = request.data.get('pharmacy_id')
        if not pharmacy_id:
            return Response(
                {"error": "pharmacy_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

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


        # --- Create Order and Items (If all validations pass) ---
        order = MedicationOrder.objects.create(
            user=request.user,
            pharmacy=pharmacy,
            prescription=prescription,
            status=MedicationOrder.StatusChoices.PENDING, # Use choices constants
            # is_delivery, delivery_address, total_amount, notes would be set later by user/pharmacy
        )

        order_items = []
        for p_item in prescription_items:
            order_item = MedicationOrderItem(
                order=order,
                prescription_item=p_item,
                medication_name_text=p_item.medication_name,
                dosage_text=p_item.dosage,
                quantity=1, # Default quantity, pharmacy might adjust
                # price_per_unit will be filled by pharmacy later
            )
            order_items.append(order_item)

        MedicationOrderItem.objects.bulk_create(order_items)

        # Serialize the newly created order
        serializer = MedicationOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MedicationOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationOrder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MedicationOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationOrder.objects.filter(user=self.request.user)

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