# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
# from django.contrib.contenttypes.fields import GenericForeignKey # Optional for linking target
# from django.contrib.contenttypes.models import ContentType       # Optional for linking target

class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('appointment', 'Appointment'), # Example specific type
        ('prescription', 'Prescription'), # Example specific type
        ('order', 'Order'),           # Example specific type
        # Add more context-specific levels as needed
    ]

    # Core Fields
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The user who should receive this notification."
    )
    verb = models.CharField(
        max_length=255,
        help_text="The main message/action description (e.g., 'Your appointment was confirmed.')"
    )
    unread = models.BooleanField(default=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')

    # Optional Fields for Context
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Actor might be deleted
        related_name='triggered_notifications', # Avoid clash with recipient relation
        null=True,
        blank=True,
        help_text="The user who initiated the action leading to the notification (optional)."
    )
    # Optional: Link to a specific object using GenericForeignKey (more flexible)
    # target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    # target_object_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    # target = GenericForeignKey('target_content_type', 'target_object_id')

    # Simpler Option: Store a URL to redirect to
    target_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="A URL the user should be directed to upon clicking the notification."
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient', 'unread']), # Index for efficient filtering
        ]

    def __str__(self):
        return f"To: {self.recipient.username} - Verb: {self.verb[:30]}..."

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save(update_fields=['unread'])

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save(update_fields=['unread'])