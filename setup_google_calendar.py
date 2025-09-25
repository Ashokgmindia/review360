#!/usr/bin/env python
"""
Setup script for Google Calendar integration.
This script helps you authorize Google Calendar access.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review360.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    print("🔧 Google Calendar Integration Setup")
    print("=" * 40)
    print()
    
    # Check if client secrets file exists
    client_secrets_file = "google_client_secrets.json"
    if not os.path.exists(client_secrets_file):
        print("❌ google_client_secrets.json file not found!")
        print("Please create this file with your Google OAuth2 credentials.")
        print("You can use the template: google_client_secrets_template.json")
        return
    
    print("✅ Client secrets file found")
    print()
    
    # Check if credentials file exists
    credentials_file = "google_credentials.json"
    if os.path.exists(credentials_file):
        print("✅ Google credentials file already exists")
        print("You can start using Google Calendar integration!")
        return
    
    print("🔐 Google Calendar Authorization Required")
    print("=" * 40)
    print()
    print("To complete the setup, you need to authorize Google Calendar access.")
    print("This is a one-time process.")
    print()
    
    # Run the authorization command
    try:
        execute_from_command_line(['manage.py', 'authorize_google_calendar'])
    except Exception as e:
        print(f"❌ Error during authorization: {e}")
        print()
        print("Manual setup instructions:")
        print("1. Run: docker compose exec web python manage.py authorize_google_calendar")
        print("2. Follow the instructions to complete OAuth2 authorization")

if __name__ == "__main__":
    main()
