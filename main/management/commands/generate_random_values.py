import random
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from main.models import User, Telemetry
import geopy.distance


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(email='msazhina23@gmail.com')

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created user with email {user.email}"))

        latitude, longitude = 60.1699, 24.9384
        total_distance = 5
        num_points = 10

        step_distance = total_distance / num_points

        start_time = now()

        for i in range(num_points):
            new_coords = self.generate_next_coords(latitude, longitude, step_distance)
            latitude, longitude = new_coords

            timestamp = start_time + timedelta(minutes=i * (60 // num_points))

            Telemetry.objects.create(
                user=user,
                latitude=latitude,
                longitude=longitude,
                ambient_temperature=random.uniform(-20, 40),
                thermostat_target_temperature=random.uniform(20, 25),
                thermostat_current_temperature=random.uniform(18, 24),
                timestamp=timestamp
            )

        self.stdout.write(self.style.SUCCESS("Successfully generated fake telemetry data!"))

    def generate_next_coords(self, latitude, longitude, step_distance_km):
        angle = random.uniform(0, 360)

        distance = step_distance_km

        origin = (latitude, longitude)
        destination = geopy.distance.distance(kilometers=distance).destination(origin, angle)

        return destination.latitude, destination.longitude
