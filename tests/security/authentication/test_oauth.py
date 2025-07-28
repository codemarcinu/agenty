#!/usr/bin/env python3
"""
Skrypt testowy do sprawdzenia konfiguracji OAuth2
"""

import os

from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels"
]

def test_oauth_config():
    """Testuje konfigurację OAuth2"""

    auth_file = "src/gmail_auth.json"

    if not os.path.exists(auth_file):
        return False

    try:
        # Wczytaj credentials
        flow = InstalledAppFlow.from_client_secrets_file(auth_file, SCOPES)


        # Użyj portu 8002 (wolny i skonfigurowany)
        flow.run_local_server(port=8002)


        return True

    except Exception:
        return False

if __name__ == "__main__":
    test_oauth_config()
