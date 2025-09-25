"""
Management command to set up Google Calendar integration.
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json


class Command(BaseCommand):
    help = 'Set up Google Calendar integration by creating client secrets file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth2 Client ID',
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Google OAuth2 Client Secret',
        )
        parser.add_argument(
            '--redirect-uris',
            type=str,
            nargs='+',
            default=['http://localhost:8080/'],
            help='Redirect URIs for OAuth2 (default: http://localhost:8080/)',
        )

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')
        redirect_uris = options.get('redirect_uris')

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.WARNING(
                    'Google Calendar integration requires OAuth2 credentials.\n'
                    'Please provide --client-id and --client-secret arguments.\n\n'
                    'To get these credentials:\n'
                    '1. Go to https://console.developers.google.com/\n'
                    '2. Create a new project or select existing one\n'
                    '3. Enable Google Calendar API\n'
                    '4. Create OAuth2 credentials\n'
                    '5. Download the JSON file and extract client_id and client_secret\n\n'
                    'Example usage:\n'
                    'python manage.py setup_google_calendar --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET'
                )
            )
            return

        # Create client secrets file
        client_secrets = {
            "installed": {
                "client_id": client_id,
                "project_id": "review360-calendar-integration",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": redirect_uris
            }
        }

        # Write client secrets file
        secrets_file = settings.GOOGLE_CLIENT_SECRETS_FILE
        os.makedirs(os.path.dirname(secrets_file), exist_ok=True)
        
        with open(secrets_file, 'w') as f:
            json.dump(client_secrets, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f'Google Calendar client secrets file created at: {secrets_file}\n'
                'You can now use Google Calendar integration features.'
            )
        )

        # Create credentials file placeholder
        credentials_file = settings.GOOGLE_CREDENTIALS_FILE
        if not os.path.exists(credentials_file):
            with open(credentials_file, 'w') as f:
                json.dump({}, f)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Credentials file placeholder created at: {credentials_file}\n'
                    'This file will be populated automatically when you first use Google Calendar features.'
                )
            )
