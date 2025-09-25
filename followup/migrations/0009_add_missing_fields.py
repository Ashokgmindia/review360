# Generated manually on 2025-09-25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('followup', '0008_create_location_objective_and_update_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='followupsession',
            name='location_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='followupsession',
            name='objective_title',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
