from rest_framework import serializers
from .models import SignatureStamp
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (minimal fields)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class SignatureStampSerializer(serializers.ModelSerializer):
    """Serializer for SignatureStamp model"""
    user = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    
    class Meta:
        model = SignatureStamp
        fields = [
            'id', 'user', 'file', 'file_url', 'file_size_mb', 
            'file_extension', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'uploaded_at', 'updated_at']
    
    def get_file_url(self, obj):
        """Return the URL of the uploaded file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def validate_file(self, value):
        """Custom validation for the uploaded file"""
        # Check file size (2MB limit)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 2MB.")
        
        # Check file extension
        allowed_extensions = ['png', 'jpg', 'jpeg']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Only {', '.join(allowed_extensions)} files are allowed."
            )
        
        return value
    
    def create(self, validated_data):
        """Create a new signature/stamp record"""
        # Set the user from the request
        user = self.context['request'].user
        validated_data['user'] = user
        
        # If user already has a signature, update it
        try:
            existing_signature = SignatureStamp.objects.get(user=user)
            existing_signature.file = validated_data['file']
            existing_signature.save()
            return existing_signature
        except SignatureStamp.DoesNotExist:
            return super().create(validated_data)


class SignatureStampUploadSerializer(serializers.ModelSerializer):
    """Simplified serializer for file upload only"""
    class Meta:
        model = SignatureStamp
        fields = ['file']
    
    def validate_file(self, value):
        """Custom validation for the uploaded file"""
        # Check file size (2MB limit)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 2MB.")
        
        # Check file extension
        allowed_extensions = ['png', 'jpg', 'jpeg']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Only {', '.join(allowed_extensions)} files are allowed."
            )
        
        return value
