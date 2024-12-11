from django.db import models
from users.models import User


class Telemetry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="telemetry")
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ambient_temperature = models.FloatField()
    thermostat_target_temperature = models.FloatField()
    thermostat_current_temperature = models.FloatField()

    def __str__(self):
        return f"Telemetry for {self.user.email} at {self.timestamp}"
