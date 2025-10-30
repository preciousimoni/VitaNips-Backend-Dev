# doctors/models.py - Add VirtualSession model at the end of the file
from django.db import models
from django.conf import settings
import uuid

class VirtualSession(models.Model):
    """Manages virtual consultation sessions via Twilio Video"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    appointment = models.OneToOneField(
        'Appointment',
        on_delete=models.CASCADE,
        related_name='virtual_session'
    )
    room_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique Twilio room identifier"
    )
    room_sid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twilio Room SID after creation"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Actual session duration"
    )
    recording_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to session recording if enabled"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Virtual Session for Appointment #{self.appointment.id} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.room_name:
            # Generate unique room name
            self.room_name = f"vitanips-{self.appointment.id}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Virtual Session"
        verbose_name_plural = "Virtual Sessions"
