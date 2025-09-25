"""
Management command to start Celery worker.
"""
from django.core.management.base import BaseCommand
import subprocess
import sys


class Command(BaseCommand):
    help = 'Start Celery worker for background tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            help='Logging level (debug, info, warning, error)',
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='Number of concurrent worker processes',
        )
        parser.add_argument(
            '--queues',
            type=str,
            default='celery',
            help='Comma-separated list of queues to consume',
        )

    def handle(self, *args, **options):
        loglevel = options['loglevel']
        concurrency = options['concurrency']
        queues = options['queues']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting Celery worker with:\n'
                f'  Log Level: {loglevel}\n'
                f'  Concurrency: {concurrency}\n'
                f'  Queues: {queues}\n'
            )
        )

        try:
            # Start Celery worker
            cmd = [
                'celery', '-A', 'review360', 'worker',
                '--loglevel', loglevel,
                '--concurrency', str(concurrency),
                '--queues', queues,
            ]
            
            subprocess.run(cmd, check=True)
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Celery worker stopped by user')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to start Celery worker: {e}')
            )
            sys.exit(1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
            sys.exit(1)
