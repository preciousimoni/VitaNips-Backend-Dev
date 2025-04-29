from rest_framework import generics, permissions, filters, status, views
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from notifications.utils import create_notification
from pharmacy.models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationOrderItem, MedicationReminder
from pharmacy.serializers import (
    PharmacySerializer, PharmacyOrderListSerializer,
    PharmacyOrderDetailSerializer, PharmacyOrderUpdateSerializer,
    MedicationSerializer, PharmacyInventorySerializer,
    MedicationOrderSerializer, MedicationReminderSerializer
)
from .permissions import IsPharmacyStaffOfOrderPharmacy
from doctors.models import Prescription, PrescriptionItem
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

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
        radius_km = self.request.query_params.get('radius', default=5)  # Default radius 5km

        if latitude and longitude:
            try:
                user_location = Point(float(longitude), float(latitude), srid=4326)  # Note: Lon, Lat order
                radius_km = float(radius_km)
                queryset = queryset.filter(
                    location__distance_lte=(user_location, D(km=radius_km))
                )
            except (ValueError, TypeError) as e:
                print(f"Error processing location parameters: {e}")  # Log the error
                pass  # Ignore invalid params for now

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

class CreateOrderFromPrescriptionView(views.APIView):
    """
    Creates a MedicationOrder from an existing Prescription.
    Expects POST request with {'pharmacy_id': <id>} in the body.
    URL: /api/prescriptions/{prescription_id}/create_order/
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, prescription_id, *args, **kwargs):
        prescription = get_object_or_404(Prescription, pk=prescription_id)
        pharmacy_id = request.data.get('pharmacy_id')

        if not pharmacy_id:
            return Response(
                {"error": "pharmacy_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pharmacy = Pharmacy.objects.get(pk=pharmacy_id)
        except Pharmacy.DoesNotExist:
            return Response(
                {"error": f"Pharmacy with ID {pharmacy_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if prescription.user != request.user:
            return Response(
                {"error": "You do not have permission to order from this prescription."},
                status=status.HTTP_403_FORBIDDEN
            )

        existing_order = MedicationOrder.objects.filter(prescription=prescription).first()
        if existing_order:
            serializer = MedicationOrderSerializer(existing_order)
            return Response(
                {"warning": "An order for this prescription already exists.", "order": serializer.data},
                status=status.HTTP_200_OK
            )

        order = MedicationOrder.objects.create(
            user=request.user,
            pharmacy=pharmacy,
            prescription=prescription,
            status='pending',
        )

        prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
        if not prescription_items.exists():
            return Response(
                {"error": "Prescription has no items to order."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order_items = []
        for p_item in prescription_items:
            order_item = MedicationOrderItem(
                order=order,
                prescription_item=p_item,
                medication_name_text=p_item.medication_name,
                dosage_text=p_item.dosage,
                quantity=1,
            )
            order_items.append(order_item)

        MedicationOrderItem.objects.bulk_create(order_items)

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
        return MedicationReminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MedicationReminderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MedicationReminder.objects.filter(user=self.request.user)