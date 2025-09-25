"""
Management command to authorize Google Calendar access for web applications.
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import json
import os


class Command(BaseCommand):
    help = 'Authorize Google Calendar access for web applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--authorization-code',
            type=str,
            help='Authorization code from Google OAuth2 flow',
        )

    def handle(self, *args, **options):
        if not GOOGLE_LIBS_AVAILABLE:
            self.stdout.write(
                self.style.ERROR(
                    'Google Calendar libraries not available. '
                    'Please install: pip install google-api-python-client google-auth google-auth-oauthlib'
                )
            )
            return

        try:
            from google_auth_oauthlib.flow import Flow
            from google.oauth2.credentials import Credentials
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    'Google Calendar libraries not available. '
                    'Please install: pip install google-api-python-client google-auth google-auth-oauthlib'
                )
            )
            return

        # Check if client secrets file exists
        if not os.path.exists(settings.GOOGLE_CLIENT_SECRETS_FILE):
            self.stdout.write(
                self.style.ERROR(
                    f'Client secrets file not found at: {settings.GOOGLE_CLIENT_SECRETS_FILE}\n'
                    'Please create the google_client_secrets.json file with your OAuth2 credentials.'
                )
            )
            return

        # Load client configuration
        with open(settings.GOOGLE_CLIENT_SECRETS_FILE, 'r') as f:
            client_config = json.load(f)

        if 'web' not in client_config:
            self.stdout.write(
                self.style.ERROR(
                    'Web application configuration not found in client secrets file.'
                )
            )
            return

        web_config = client_config['web']
        client_id = web_config['client_id']
        client_secret = web_config['client_secret']
        redirect_uri = 'http://localhost:8080/'

        # Create the authorization URL
        flow = Flow.from_client_config(client_config, SCOPES)
        flow.redirect_uri = redirect_uri

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Google Calendar Authorization Required\n'
                '=====================================\n\n'
                '1. Open this URL in your browser:\n'
                f'{authorization_url}\n\n'
                '2. Complete the authorization process\n'
                '3. Copy the authorization code from the redirect URL\n'
                '4. Run this command with the authorization code:\n'
                'python manage.py authorize_google_calendar --authorization-code YOUR_CODE_HERE\n'
            )
        )

        # If authorization code is provided, exchange it for tokens
        auth_code = options.get('authorization_code')
        if auth_code:
            try:
                flow.fetch_token(code=auth_code)
                credentials = flow.credentials

                # Save credentials
                os.makedirs(os.path.dirname(settings.GOOGLE_CREDENTIALS_FILE), exist_ok=True)
                with open(settings.GOOGLE_CREDENTIALS_FILE, 'w') as token_file:
                    token_file.write(credentials.to_json())

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Google Calendar authorization successful!\n'
                        f'Credentials saved to: {settings.GOOGLE_CREDENTIALS_FILE}\n'
                        'You can now use Google Calendar integration features.'
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Authorization failed: {e}\n'
                        'Please try again with a fresh authorization code.'
                    )
                )


# Import required modules
try:
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    GOOGLE_LIBS_AVAILABLE = True
    SCOPES = ['https://www.googleapis.com/auth/calendar']
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    SCOPES = []
