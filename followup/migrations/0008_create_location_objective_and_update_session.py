# Generated manually on 2025-09-25

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('followup', '0007_field_objective'),
        ('iam', '0001_initial'),
    ]

    operations = [
        # Create Location model (tell Django about the model)
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Name of the location (e.g., 'Classroom A', 'Library', 'Online')", max_length=255)),
                ('description', models.TextField(blank=True, default='', help_text='Description of the location')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('college', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup_locations', to='iam.college')),
            ],
        ),
        # Create the table if it doesn't exist (handle existing table)
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS followup_location (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                college_id BIGINT NOT NULL REFERENCES iam_college(id) ON DELETE CASCADE
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS followup_location;"
        ),
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['college', 'is_active'], name='followup_lo_college_c011a4_idx'),
        ),
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['name'], name='followup_lo_name_78e0f9_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='location',
            unique_together={('college', 'name')},
        ),
        
        # Add new fields to FollowUpSession
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
        
        # First make location and objective fields nullable
        migrations.RunSQL(
            "ALTER TABLE followup_followupsession ALTER COLUMN location DROP NOT NULL;",
            reverse_sql="ALTER TABLE followup_followupsession ALTER COLUMN location SET NOT NULL;"
        ),
        migrations.RunSQL(
            "ALTER TABLE followup_followupsession ALTER COLUMN objective DROP NOT NULL;",
            reverse_sql="ALTER TABLE followup_followupsession ALTER COLUMN objective SET NOT NULL;"
        ),
        # Then clear existing data
        migrations.RunSQL(
            "UPDATE followup_followupsession SET location = NULL, objective = NULL;",
            reverse_sql="-- No reverse operation needed"
        ),
        
        # Convert location field to foreign key
        migrations.AlterField(
            model_name='followupsession',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='follow_up_sessions', to='followup.location'),
        ),
        
        # Convert objective field to foreign key
        migrations.AlterField(
            model_name='followupsession',
            name='objective',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='follow_up_sessions', to='followup.objective'),
        ),
        
        # Delete the old Field model
        migrations.DeleteModel(
            name='Field',
        ),
    ]
