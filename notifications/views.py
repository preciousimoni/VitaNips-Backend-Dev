# notifications/views.py
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.pagination import PageNumberPagination
from push_notifications.models import APNSDevice, GCMDevice

class DeviceRegistrationView(views.APIView):
    """
    Handles registration of user devices for push notifications.
    Expects POST request with:
    {
        "registration_id": "YOUR_DEVICE_TOKEN_OR_FCM_ID",
        "type": "web" | "ios" | "android"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        registration_id = request.data.get('registration_id')
        device_type = request.data.get('type', '').lower() # 'web', 'ios', 'android'

        if not registration_id:
            return Response({"error": "registration_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        if device_type not in ['web', 'ios', 'android']:
             return Response({"error": "Invalid or missing 'type'. Must be 'web', 'ios', or 'android'."}, status=status.HTTP_400_BAD_REQUEST)

        created = False
        try:
            if device_type == 'ios':
                # Use APNSDevice for iOS
                # device_id is optional - registration_id is key here
                device, created = APNSDevice.objects.update_or_create(
                    registration_id=registration_id,
                    defaults={'user': user, 'active': True}
                )
            else:
                # Use GCMDevice for Android and Web (FCM)
                # cloud_message_type determines FCM/GCM, defaults often work for FCM
                device, created = GCMDevice.objects.update_or_create(
                    registration_id=registration_id,
                    defaults={'user': user, 'active': True, 'cloud_message_type': 'FCM'} # Be explicit for FCM
                )

            # Optional: Deactivate other devices for the same user if only one active device is desired
            # e.g., GCMDevice.objects.filter(user=user).exclude(pk=device.pk).update(active=False)

            action = "registered" if created else "updated"
            return Response(
                {"detail": f"Device {action} successfully."},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except Exception as e:
            # Log the error for debugging
            print(f"Error registering device for user {user.id}: {e}")
            return Response({"error": "Failed to register device."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50

class NotificationListView(generics.ListAPIView):
    """Lists notifications for the logged-in user. Supports filtering by 'unread'."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        unread_filter = self.request.query_params.get('unread')
        if unread_filter is not None:
            is_unread = unread_filter.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(unread=is_unread)
        return queryset

class MarkNotificationAsReadView(views.APIView):
    """Marks a specific notification as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.mark_as_read()
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarkAllNotificationsAsReadView(views.APIView):
    """Marks all unread notifications for the user as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            updated_count = Notification.objects.filter(recipient=request.user, unread=True).update(unread=False)
            return Response({"status": f"{updated_count} notifications marked as read"}, status=status.HTTP_200_OK)
        except Exception as e:
             # Log error e
             return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnreadNotificationCountView(views.APIView):
     """Returns the count of unread notifications."""
     permission_classes = [permissions.IsAuthenticated]

     def get(self, request, *args, **kwargs):
         try:
             count = Notification.objects.filter(recipient=request.user, unread=True).count()
             return Response({"unread_count": count}, status=status.HTTP_200_OK)
         except Exception as e:
              # Log error e
              return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)