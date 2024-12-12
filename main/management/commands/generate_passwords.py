import random
import string
from django.core.management.base import BaseCommand
from main.models import LoginPassword


class Command(BaseCommand):
    help = 'Generate random passwords for login'

    def handle(self, *args, **kwargs):
        for _ in range(10):
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            if not LoginPassword.objects.filter(password=password).exists():
                LoginPassword.objects.create(password=password)
                self.stdout.write(self.style.SUCCESS(f"Password generated: {password}"))
