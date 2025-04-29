# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('appointment', 'Appointment'),
        ('prescription', 'Prescription'),
        ('order', 'Order'),
    ]

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

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='triggered_notifications',
        null=True,
        blank=True,
        help_text="The user who initiated the action leading to the notification (optional)."
    )

    target_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="A URL the user should be directed to upon clicking the notification."
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient', 'unread']),
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