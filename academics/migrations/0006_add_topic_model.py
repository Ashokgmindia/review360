# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0005_remove_student_bulk_upload_errors_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
                ('order', models.PositiveIntegerField(default=0, help_text='Order of the topic within the subject')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='academics.subject')),
            ],
            options={
                'ordering': ['order', 'name'],
                'indexes': [
                    models.Index(fields=['subject', 'order'], name='academics_topic_subject_order_idx'),
                    models.Index(fields=['subject', 'is_active'], name='academics_topic_subject_active_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='topic',
            constraint=models.UniqueConstraint(fields=('subject', 'name'), name='academics_topic_subject_name_unique'),
        ),
    ]

