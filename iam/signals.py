from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def ensure_superadmin_role(sender, instance: User, created, **kwargs):
    # Force role to Super Admin when user is a superuser
    if instance.is_superuser and instance.role != User.Role.SUPERADMIN:
        User.objects.filter(pk=instance.pk).update(role=User.Role.SUPERADMIN, is_staff=True)


