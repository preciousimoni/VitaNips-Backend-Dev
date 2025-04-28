# notifications/views.py
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.pagination import PageNumberPagination # Import pagination

# Optional: Define a standard pagination class for notifications
class NotificationPagination(PageNumberPagination):
    page_size = 15 # Number of notifications per page
    page_size_query_param = 'page_size'
    max_page_size = 50

class NotificationListView(generics.ListAPIView):
    """Lists notifications for the logged-in user. Supports filtering by 'unread'."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination # Apply pagination

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        unread_filter = self.request.query_params.get('unread')
        if unread_filter is not None:
            is_unread = unread_filter.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(unread=is_unread)
        return queryset # Default ordering is '-timestamp' from model Meta

class MarkNotificationAsReadView(views.APIView):
    """Marks a specific notification as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.mark_as_read()
            # Return the updated notification object
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found or permission denied."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             # Log error e
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