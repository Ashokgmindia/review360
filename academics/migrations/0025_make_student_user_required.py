# Generated manually to handle existing students without user accounts

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


def create_users_for_existing_students(apps, schema_editor):
    """Create user accounts for existing students that don't have them."""
    Student = apps.get_model('academics', 'Student')
    User = apps.get_model('iam', 'User')
    
    # Find students without user accounts
    students_without_users = Student.objects.filter(user__isnull=True)
    
    for student in students_without_users:
        # Generate username from email or first_name + last_name
        if student.email:
            username = student.email
            email = student.email
        else:
            username = f"{student.first_name.lower()}.{student.last_name.lower()}"
            email = f"{username}@student.local"
        
        # Check if user already exists
        if not User.objects.filter(username=username).exists():
            # Create the user directly (not using create_user method in migrations)
            user = User.objects.create(
                username=username,
                email=email,
                password='pbkdf2_sha256$600000$temp$temp',  # Temporary password hash
                role='student',
                college=student.college,
                first_name=student.first_name,
                last_name=student.last_name,
                phone_number=student.phone_number,
                is_active=True,
            )
            
            # Add user to college's member users
            if student.college:
                user.colleges.add(student.college)
            
            # Link the student to the user
            student.user = user
            student.save()


def reverse_create_users_for_existing_students(apps, schema_editor):
    """Reverse operation - this would be complex to implement safely, so we'll leave it as no-op."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0024_studenttopicprogress'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # First, create users for existing students
        migrations.RunPython(
            create_users_for_existing_students,
            reverse_create_users_for_existing_students,
        ),
        
        # Then make the user field required
        migrations.AlterField(
            model_name='student',
            name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='student_profile', 
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
