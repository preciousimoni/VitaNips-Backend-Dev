# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class NotificationTemplate(models.Model):
    """Reusable templates for different notification types"""
    TEMPLATE_TYPES = [
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('prescription_ready', 'Prescription Ready'),
        ('refill_reminder', 'Medication Refill Reminder'),
        ('medication_adherence', 'Medication Adherence'),
        ('order_status', 'Order Status Update'),
        ('test_results', 'Test Results Available'),
        ('emergency_alert', 'Emergency Alert'),
        ('health_insight', 'Health Insight'),
        ('appointment_followup', 'Appointment Follow-up'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    
    # Multi-channel templates
    email_subject = models.CharField(max_length=200, blank=True)
    email_body_html = models.TextField(blank=True, help_text="HTML template with {{variables}}")
    email_body_text = models.TextField(blank=True, help_text="Plain text fallback")
    
    sms_body = models.CharField(max_length=160, blank=True, help_text="SMS limited to 160 chars")
    
    push_title = models.CharField(max_length=100, blank=True)
    push_body = models.CharField(max_length=200, blank=True)
    
    in_app_message = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    def render(self, context, channel='email'):
        """Render template with context variables"""
        from django.template import Template, Context as DjangoContext
        
        if channel == 'email':
            subject_template = Template(self.email_subject)
            body_template = Template(self.email_body_html)
            return {
                'subject': subject_template.render(DjangoContext(context)),
                'body': body_template.render(DjangoContext(context))
            }
        elif channel == 'sms':
            sms_template = Template(self.sms_body)
            return sms_template.render(DjangoContext(context))
        elif channel == 'push':
            title_template = Template(self.push_title)
            body_template = Template(self.push_body)
            return {
                'title': title_template.render(DjangoContext(context)),
                'body': body_template.render(DjangoContext(context))
            }
        elif channel == 'in_app':
            message_template = Template(self.in_app_message)
            return message_template.render(DjangoContext(context))


class Notification(models.Model):
    """Enhanced notification model with delivery tracking"""
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('appointment', 'Appointment'),
        ('prescription', 'Prescription'),
        ('medication', 'Medication'),
        ('order', 'Order'),
        ('health', 'Health'),
        ('emergency', 'Emergency'),
        ('system', 'System'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Template-based notifications
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template used to generate this notification"
    )
    
    # Content
    title = models.CharField(max_length=200)
    verb = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    
    # Action tracking
    action_url = models.URLField(max_length=500, null=True, blank=True)
    action_text = models.CharField(max_length=100, null=True, blank=True)
    
    # Related object (polymorphic)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Actor
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='triggered_notifications',
        null=True,
        blank=True
    )
    
    # Status
    unread = models.BooleanField(default=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="Schedule for future delivery")
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient', 'unread', '-timestamp']),
            models.Index(fields=['recipient', 'category', '-timestamp']),
            models.Index(fields=['scheduled_for']),
        ]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.read_at = timezone.now()
            self.save(update_fields=['unread', 'read_at'])
    
    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.read_at = None
            self.save(update_fields=['unread', 'read_at'])
    
    def dismiss(self):
        self.dismissed = True
        self.dismissed_at = timezone.now()
        self.save(update_fields=['dismissed', 'dismissed_at'])


class NotificationDelivery(models.Model):
    """Track multi-channel delivery attempts"""
    CHANNEL_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('clicked', 'Clicked'),
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Delivery details
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # External service tracking
    external_id = models.CharField(max_length=255, blank=True, help_text="Message ID from provider")
    provider_response = models.JSONField(default=dict, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Notification Deliveries"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['status', 'next_retry_at']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} - {self.channel} - {self.status}"


class NotificationPreference(models.Model):
    """Granular per-user notification preferences"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Global toggles
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Category preferences (JSON for flexibility)
    # Example: {'appointment': {'email': True, 'sms': True, 'push': True}, ...}
    category_preferences = models.JSONField(default=dict, blank=True)
    
    # Frequency limits (prevent notification fatigue)
    max_daily_emails = models.IntegerField(default=10)
    max_daily_sms = models.IntegerField(default=5)
    
    # Digest settings
    digest_enabled = models.BooleanField(default=False)
    digest_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly')],
        default='daily'
    )
    digest_time = models.TimeField(default='09:00')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
    
    def should_send_now(self):
        """Check if notification should be sent based on quiet hours"""
        if not self.quiet_hours_enabled:
            return True
        
        now = timezone.localtime(timezone.now()).time()
        if self.quiet_hours_start < self.quiet_hours_end:
            return not (self.quiet_hours_start <= now <= self.quiet_hours_end)
        else:  # Quiet hours span midnight
            return not (self.quiet_hours_start <= now or now <= self.quiet_hours_end)
    
    def get_channel_preference(self, category, channel):
        """Get user preference for specific category and channel"""
        if category not in self.category_preferences:
            return True  # Default to enabled
        
        category_prefs = self.category_preferences[category]
        return category_prefs.get(channel, True)


class NotificationSchedule(models.Model):
    """Scheduled recurring notifications (e.g., medication reminders)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Schedule configuration
    is_active = models.BooleanField(default=True)
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('once', 'One-time'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    time_of_day = models.TimeField()
    days_of_week = models.JSONField(default=list, blank=True, help_text="[0-6] for Mon-Sun")
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Context data for template rendering
    context_data = models.JSONField(default=dict)
    
    # Tracking
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField(null=True, blank=True, db_index=True)
    total_sent = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.template.name} for {self.user.email} - {self.frequency}"