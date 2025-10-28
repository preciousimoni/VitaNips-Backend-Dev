# emergency/views.py
from rest_framework import generics, views, permissions, status
from rest_framework.response import Response
from .tasks import send_sos_alerts_task
from .models import EmergencyService, EmergencyContact, EmergencyAlert
from .serializers import (
    EmergencyServiceSerializer, EmergencyContactSerializer, EmergencyAlertSerializer
)
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
import logging

logger = logging.getLogger(__name__)

class TriggerSOSView(views.APIView):
    """
    Receives SOS trigger from frontend, queues background task to send alerts.
    Expects POST data: {'latitude': float, 'longitude': float, 'message': str (optional)}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        message = request.data.get('message', None)

        if latitude is None or longitude is None:
            return Response(
                {"error": "Latitude and Longitude are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat_float = float(latitude)
            lon_float = float(longitude)
            if not (-90 <= lat_float <= 90 and -180 <= lon_float <= 180):
                raise ValueError("Invalid latitude or longitude range.")
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid latitude or longitude format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Try to queue the task asynchronously with Celery
            send_sos_alerts_task.delay(
                user_id=request.user.id,
                latitude=lat_float,
                longitude=lon_float,
                message=message
            )
            return Response(
                {"status": "SOS signal received and processing initiated."},
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            # If Celery/Redis is not available, execute the task synchronously
            logger.warning(f"Celery unavailable for user {request.user.id}: {e}. Running SOS task synchronously.")
            try:
                # Execute the task function directly (synchronously)
                send_sos_alerts_task(
                    user_id=request.user.id,
                    latitude=lat_float,
                    longitude=lon_float,
                    message=message
                )
                return Response(
                    {"status": "SOS signal received and processed."},
                    status=status.HTTP_200_OK
                )
            except Exception as sync_error:
                logger.error(f"ERROR executing SOS task synchronously for user {request.user.id}: {sync_error}")
                return Response(
                    {"error": "Could not initiate SOS alert process. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

class EmergencyServiceListView(generics.ListAPIView):
    serializer_class = EmergencyServiceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = EmergencyService.objects.all()

        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lon')
        radius_km_str = self.request.query_params.get('radius', default='5') # Default radius 5km

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

        service_type = self.request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        return queryset.order_by('name')

class EmergencyContactListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)

class EmergencyAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmergencyAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyAlert.objects.filter(user=self.request.user)