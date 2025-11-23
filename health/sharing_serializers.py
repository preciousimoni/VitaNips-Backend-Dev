from rest_framework import serializers
from .sharing_models import DocumentShare, DocumentAccessLog
from users.serializers import UserSerializer

class DocumentShareSerializer(serializers.ModelSerializer):
    shared_with_email = serializers.ReadOnlyField(source='shared_with.email')
    shared_by_email = serializers.ReadOnlyField(source='shared_by.email')
    document_title = serializers.ReadOnlyField(source='document.description')

    class Meta:
        model = DocumentShare
        fields = [
            'id', 'document', 'document_title', 'shared_with', 'shared_with_email',
            'shared_by', 'shared_by_email', 'permission', 'expires_at',
            'created_at', 'accessed_at'
        ]
        read_only_fields = ['shared_by', 'created_at', 'accessed_at']

class DocumentAccessLogSerializer(serializers.ModelSerializer):
    accessed_by_name = serializers.ReadOnlyField(source='accessed_by.get_full_name')

    class Meta:
        model = DocumentAccessLog
        fields = [
            'id', 'document', 'accessed_by', 'accessed_by_name',
            'action', 'ip_address', 'accessed_at'
        ]
        read_only_fields = ['accessed_at']

