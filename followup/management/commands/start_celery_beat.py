"""
Management command to start Celery Beat scheduler.
"""
from django.core.management.base import BaseCommand
import subprocess
import sys


class Command(BaseCommand):
    help = 'Start Celery Beat scheduler for periodic tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            help='Logging level (debug, info, warning, error)',
        )

    def handle(self, *args, **options):
        loglevel = options['loglevel']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting Celery Beat scheduler with log level: {loglevel}\n'
            )
        )

        try:
            # Start Celery Beat
            cmd = [
                'celery', '-A', 'review360', 'beat',
                '--loglevel', loglevel,
            ]
            
            subprocess.run(cmd, check=True)
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Celery Beat stopped by user')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to start Celery Beat: {e}')
            )
            sys.exit(1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
            sys.exit(1)
