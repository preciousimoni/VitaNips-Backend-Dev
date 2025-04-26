from rest_framework import generics, permissions, filters
from .models import Pharmacy, Medication, PharmacyInventory, MedicationOrder, MedicationReminder
from .serializers import (
    PharmacySerializer, MedicationSerializer, PharmacyInventorySerializer,
    MedicationOrderSerializer, MedicationReminderSerializer
)
from django.db.models import Q
from haversine import haversine, Unit

class PharmacyListView(generics.ListAPIView):
    serializer_class = PharmacySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address']

    def get_queryset(self):
        """
        Optionally filter pharmacies by proximity if lat, lon, and radius params are provided.
        """
        queryset = Pharmacy.objects.all() # Start with all pharmacies

        # --- Proximity Filtering ---
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lon')
        radius_km = self.request.query_params.get('radius', default=5) # Default radius 5km

        if latitude and longitude:
            try:
                user_location = (float(latitude), float(longitude))
                radius_km = float(radius_km)

                # --- Option A: Simple Haversine Filtering (Less performant for large datasets) ---
                pharmacy_ids_in_radius = []
                # Iterate through potentially ALL pharmacies in the DB
                for pharmacy in queryset.filter(latitude__isnull=False, longitude__isnull=False):
                    pharmacy_location = (pharmacy.latitude, pharmacy.longitude)
                    distance = haversine(user_location, pharmacy_location, unit=Unit.KILOMETERS)
                    if distance <= radius_km:
                        pharmacy_ids_in_radius.append(pharmacy.id)

                queryset = queryset.filter(id__in=pharmacy_ids_in_radius)

                # --- Option B: GeoDjango Filtering (Requires PostGIS setup, much more performant) ---
                # Requires Pharmacy model to have a PointField (e.g., `location = PointField()`)
                # from django.contrib.gis.geos import Point
                # from django.contrib.gis.measure import D
                #
                # if hasattr(Pharmacy, 'location'): # Check if model uses PointField
                #     user_point = Point(float(longitude), float(latitude), srid=4326) # Note: Lon, Lat order
                #     queryset = queryset.filter(location__distance_lte=(user_point, D(km=radius_km)))
                # else:
                #     # Fallback or raise error if GeoDjango expected but not set up
                #     pass

            except (ValueError, TypeError) as e:
                # Handle invalid lat/lon/radius parameters gracefully (e.g., ignore them)
                print(f"Error processing location parameters: {e}") # Log the error
                # Optionally return an empty queryset or raise an APIException
                # return Pharmacy.objects.none()
                pass # Ignoring invalid params for now

        # --- End Proximity Filtering ---

        # Add other filters here if needed (e.g., offers_delivery, is_24_hours)
        offers_delivery = self.request.query_params.get('offers_delivery')
        if offers_delivery is not None:
             queryset = queryset.filter(offers_delivery=str(offers_delivery).lower() in ['true', '1'])

        is_24_hours = self.request.query_params.get('is_24_hours')
        if is_24_hours is not None:
             queryset = queryset.filter(is_24_hours=str(is_24_hours).lower() in ['true', '1'])


        return queryset.order_by('name')

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