# notifications/urls.py
from django.urls import path
from .views import (
    NotificationListView,
    MarkNotificationAsReadView,
    MarkAllNotificationsAsReadView,
    UnreadNotificationCountView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('unread_count/', UnreadNotificationCountView.as_view(), name='unread-count'), # Changed URL slightly
    path('<int:pk>/read/', MarkNotificationAsReadView.as_view(), name='mark-read'),
    path('read_all/', MarkAllNotificationsAsReadView.as_view(), name='mark-all-read'),
]