from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, College


@receiver(post_save, sender=User)
def ensure_superadmin_role(sender, instance: User, created, **kwargs):
    # Force role to Super Admin when user is a superuser
    if instance.is_superuser and instance.role != User.Role.SUPERADMIN:
        User.objects.filter(pk=instance.pk).update(role=User.Role.SUPERADMIN, is_staff=True)


@receiver(post_save, sender=College)
def sync_college_admin(sender, instance: College, created, **kwargs):
    # When a college's admin is set/changed, ensure the user reflects this
    admin_user = instance.admin
    if not admin_user:
        return
    updates = {}
    if admin_user.role != User.Role.COLLEGE_ADMIN:
        updates["role"] = User.Role.COLLEGE_ADMIN
    if admin_user.college_id != instance.id:
        updates["college_id"] = instance.id
    if admin_user.is_staff is not True:
        updates["is_staff"] = True
    if updates:
        User.objects.filter(pk=admin_user.pk).update(**updates)


