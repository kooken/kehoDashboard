from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User

class TelemetrySerializer(serializers.Serializer):
    dTime = serializers.CharField(max_length=255)  # or IntegerField if needed
    dLat = serializers.FloatField()
    dLong = serializers.FloatField()
    ambT = serializers.FloatField()
    curT = serializers.FloatField()
    targT = serializers.FloatField()
    mode = serializers.IntegerField()

class UserSerializer(serializers.ModelSerializer):
    telemetry = TelemetrySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'telemetry']

class TelemetryDataSerializer(serializers.Serializer):
    client_id = serializers.CharField(max_length=255)
    first_time = serializers.DateTimeField()
    first_lat = serializers.FloatField()
    first_long = serializers.FloatField()
    first_ambT = serializers.FloatField()
    first_curT = serializers.FloatField()
    first_trgT = serializers.FloatField()
    mode = serializers.IntegerField()
    d = serializers.ListField(
        child=TelemetrySerializer()
    )
