from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import MedicalDocument
from .sharing_models import DocumentShare
from .sharing_serializers import DocumentShareSerializer
from .permissions import IsOwnerOrSharedWith
from notifications.utils import create_notification

class DocumentShareCreateView(generics.CreateAPIView):
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.validated_data['document']
        if document.user != self.request.user:
            raise permissions.PermissionDenied("You can only share your own documents.")
            
        share = serializer.save(shared_by=self.request.user)
        
        # Notify recipient
        create_notification(
            recipient=share.shared_with,
            actor=self.request.user,
            verb=f"{self.request.user.get_full_name()} shared a document with you: {document.description}",
            level='info',
            target_url=f"/documents/{document.id}"
        )

class SharedWithMeListView(generics.ListAPIView):
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DocumentShare.objects.filter(
            shared_with=self.request.user
        ).filter(
            models.Q(expires_at__gt=timezone.now()) | models.Q(expires_at__isnull=True)
        ).select_related('document', 'shared_by')

class DocumentShareListView(generics.ListAPIView):
    """List users a document is shared with"""
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        document_id = self.kwargs['pk']
        document = get_object_or_404(MedicalDocument, pk=document_id)
        if document.user != self.request.user:
            raise permissions.PermissionDenied
        return DocumentShare.objects.filter(document_id=document_id)

class DocumentShareDeleteView(generics.DestroyAPIView):
    queryset = DocumentShare.objects.all()
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.document.user != self.request.user:
            raise permissions.PermissionDenied("You can only revoke shares for your own documents.")
        instance.delete()

