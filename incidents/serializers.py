from django.contrib.auth import get_user_model
from rest_framework import serializers
from incidents.models import Incident, DigestLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'location', 'concerns', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def validate_concerns(self, value):
        valid_concerns = {'physical', 'digital', 'weather'}
        invalid = set(value) - valid_concerns
        if invalid:
            raise serializers.ValidationError(
                f"Invalid concern types: {invalid}. Must be one of {valid_concerns}"
            )
        return value


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'location', 'source',
            'category', 'severity', 'is_noise', 'action_steps',
            'is_enriched', 'ai_enriched', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'category', 'severity', 'is_noise', 'action_steps',
            'is_enriched', 'ai_enriched', 'created_at', 'updated_at',
        ]

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value.strip()

    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters.")
        return value.strip()

    def validate_location(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Location must be at least 3 characters.")
        return value.strip()


class DigestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DigestLog
        fields = ['id', 'user', 'generated_at', 'ai_used', 'result_json']
        read_only_fields = ['id', 'generated_at']