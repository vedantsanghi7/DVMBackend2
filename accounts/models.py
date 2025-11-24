from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class PassengerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"