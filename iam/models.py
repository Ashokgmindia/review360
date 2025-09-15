from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager


class College(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    postcode = models.CharField(max_length=20, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)
    admin = models.ForeignKey(
        "iam.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_of_colleges",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.name or self.code


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "superadmin", "Super Admin"
        COLLEGE_ADMIN = "college_admin", "College Admin"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    # Backward-compat single-college reference kept for legacy flows
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    # New: support users belonging to multiple colleges
    colleges = models.ManyToManyField(College, related_name="member_users", blank=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    employee_id = models.CharField(max_length=50, blank=True, default="")
    designation = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.email or self.username

    def save(self, *args, **kwargs):
        # Ensure superusers always have proper flags and role
        if self.is_superuser:
            self.is_staff = True
            self.role = self.Role.SUPERADMIN
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        if email:
            email = self.normalize_email(email)
        extra_fields.setdefault("role", User.Role.STUDENT)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields["role"] = User.Role.SUPERADMIN
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, email, password, **extra_fields)


User.add_to_class("objects", UserManager())


