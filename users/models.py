from django.contrib.auth.models import AbstractUser
from django.db import models
from users.managers import CustomUserManager


# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    token = models.CharField(max_length=100, verbose_name='Token', null=True, blank=True)
    display_name = models.CharField(max_length=100, verbose_name='Display Name', null=True, blank=True)

    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
