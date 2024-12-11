from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User, Telemetry


class TelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetry
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    telemetry = TelemetrySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'telemetry']
