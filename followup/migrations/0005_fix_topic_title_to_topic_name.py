# Generated manually to fix database schema mismatch

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('followup', '0004_add_student_topic_progress_to_followup'),
    ]

    operations = [
        # Add topic_name field if it doesn't exist, and remove topic_title if it exists
        migrations.RunSQL(
            """
            DO $$ 
            BEGIN
                -- Add topic_name if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'followup_followupsession' 
                    AND column_name = 'topic_name'
                ) THEN
                    ALTER TABLE followup_followupsession ADD COLUMN topic_name VARCHAR(255) DEFAULT '';
                END IF;
                
                -- Remove topic_title if it exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'followup_followupsession' 
                    AND column_name = 'topic_title'
                ) THEN
                    ALTER TABLE followup_followupsession DROP COLUMN topic_title;
                END IF;
            END $$;
            """,
            reverse_sql="""
            DO $$ 
            BEGIN
                -- Add topic_title if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'followup_followupsession' 
                    AND column_name = 'topic_title'
                ) THEN
                    ALTER TABLE followup_followupsession ADD COLUMN topic_title VARCHAR(255) DEFAULT '';
                END IF;
                
                -- Remove topic_name if it exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'followup_followupsession' 
                    AND column_name = 'topic_name'
                ) THEN
                    ALTER TABLE followup_followupsession DROP COLUMN topic_name;
                END IF;
            END $$;
            """,
        ),
    ]
