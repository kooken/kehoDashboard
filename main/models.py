from django.db import models
from users.models import User


class Telemetry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="telemetry")
    timestamp = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ambient_temperature = models.FloatField()
    thermostat_target_temperature = models.FloatField()
    thermostat_current_temperature = models.FloatField()

    def __str__(self):
        return f"Telemetry for {self.user.email} at {self.timestamp}"


class LoginPassword(models.Model):
    password = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.password


class WeatherForecast(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    weather_description = models.CharField(max_length=255, null=True, blank=True)
    forecast_time = models.DateTimeField()

    def __str__(self):
        return f"Weather at ({self.latitude}, {self.longitude}) on {self.forecast_time}"
