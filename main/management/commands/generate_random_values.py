import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import User, Telemetry
import geopy.distance
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(email='test@mail.com')

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created user with email {user.email}"))

        latitude, longitude = 60.1699, 24.9384
        total_distance = 5
        num_points = 10

        step_distance = total_distance / num_points

        start_time = timezone.now()

        for i in range(num_points):
            new_coords = self.generate_next_coords(latitude, longitude, step_distance)
            latitude, longitude = new_coords

            timestamp = start_time + relativedelta(minutes=5 * i)
            print("Current timestamp is:", timestamp)

            timestamp = timestamp.replace(microsecond=0)
            print("Updated timestamp is:", timestamp)

            Telemetry.objects.create(
                user=user,
                latitude=latitude,
                longitude=longitude,
                ambient_temperature=random.uniform(-20, 40),
                thermostat_target_temperature=random.uniform(20, 25),
                thermostat_current_temperature=random.uniform(18, 24),
                timestamp=timestamp
            )
            print("Current telemetry object is:", Telemetry)

        self.stdout.write(self.style.SUCCESS("Successfully generated fake telemetry data!"))

    def generate_next_coords(self, latitude, longitude, step_distance_km):
        angle = random.uniform(0, 360)

        origin = (latitude, longitude)
        destination = geopy.distance.distance(kilometers=step_distance_km).destination(origin, angle)

        return destination.latitude, destination.longitude
