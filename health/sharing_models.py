from django.db import models
from django.conf import settings
from django.utils import timezone

class DocumentShare(models.Model):
    PERMISSION_CHOICES = (
        ('view', 'View'),
        ('download', 'Download'),
    )

    document = models.ForeignKey('health.MedicalDocument', on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_documents')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_shares')
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='view')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document} shared with {self.shared_with} by {self.shared_by}"

class DocumentAccessLog(models.Model):
    ACTION_CHOICES = (
        ('view', 'View'),
        ('download', 'Download'),
        ('share', 'Share'),
    )

    document = models.ForeignKey('health.MedicalDocument', on_delete=models.CASCADE, related_name='access_logs')
    accessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.document} accessed by {self.accessed_by} ({self.action})"

