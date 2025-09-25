"""
Management command to test Celery functionality.
"""
from django.core.management.base import BaseCommand
from followup.tasks import send_session_reminders, cleanup_old_sessions, sync_calendar_events
from celery import current_app
import time


class Command(BaseCommand):
    help = 'Test Celery functionality and background tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-task',
            type=str,
            choices=['reminders', 'cleanup', 'sync', 'all'],
            default='all',
            help='Which task to test',
        )

    def handle(self, *args, **options):
        test_task = options['test_task']
        
        self.stdout.write(
            self.style.SUCCESS('Testing Celery functionality...\n')
        )

        # Test Celery connection
        try:
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                self.stdout.write(
                    self.style.SUCCESS('✅ Celery workers are running')
                )
                for worker, info in stats.items():
                    self.stdout.write(f'  Worker: {worker}')
                    self.stdout.write(f'  Status: {info.get("status", "unknown")}')
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  No Celery workers found')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Celery connection failed: {e}')
            )
            return

        # Test specific tasks
        if test_task in ['reminders', 'all']:
            self.stdout.write('\n📧 Testing session reminders task...')
            try:
                result = send_session_reminders.delay()
                self.stdout.write(f'✅ Reminders task queued: {result.id}')
                self.stdout.write('   This task will send reminders for sessions starting in 24 hours')
            except Exception as e:
                self.stdout.write(f'❌ Reminders task failed: {e}')

        if test_task in ['cleanup', 'all']:
            self.stdout.write('\n🧹 Testing cleanup task...')
            try:
                result = cleanup_old_sessions.delay()
                self.stdout.write(f'✅ Cleanup task queued: {result.id}')
                self.stdout.write('   This task will clean up old completed sessions')
            except Exception as e:
                self.stdout.write(f'❌ Cleanup task failed: {e}')

        if test_task in ['sync', 'all']:
            self.stdout.write('\n📅 Testing calendar sync task...')
            try:
                result = sync_calendar_events.delay()
                self.stdout.write(f'✅ Calendar sync task queued: {result.id}')
                self.stdout.write('   This task will sync calendar events')
            except Exception as e:
                self.stdout.write(f'❌ Calendar sync task failed: {e}')

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Celery testing completed!')
        )
        self.stdout.write(
            'Check the Celery worker logs to see task execution results.'
        )
