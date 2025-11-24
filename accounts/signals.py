from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PassengerProfile


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        PassengerProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile_when_user_saved(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
