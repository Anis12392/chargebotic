"""
One-time Google OAuth setup.
Run this once after placing credentials.json in the project root.
Opens a browser, asks you to authorize, then saves token.json.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

# credentials.json and token.json live at the repo root (~/claude-code-official-memory),
# which is where every Drive/Docs/Slides script reads them from. The project folder is
# checked as a fallback so an older layout keeps working.
REPO_ROOT = os.path.expanduser("~/claude-code-official-memory")
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

CREDS_PATH = next(
    (p for p in (
        os.path.join(REPO_ROOT, "credentials.json"),
        os.path.join(PROJECT_ROOT, "credentials.json"),
    ) if os.path.exists(p)),
    os.path.join(REPO_ROOT, "credentials.json"),
)
TOKEN_PATH = os.path.join(os.path.dirname(CREDS_PATH), "token.json")


def main():
    if not os.path.exists(CREDS_PATH):
        print(f"\n❌  credentials.json not found at: {CREDS_PATH}")
        print("\nFollow these steps:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project (or select existing)")
        print("  3. Enable APIs: Google Drive API + Google Slides API + Google Docs API")
        print("  4. Go to APIs & Services → Credentials")
        print("  5. Create Credentials → OAuth 2.0 Client ID → Desktop app")
        print("  6. Download the JSON → rename it 'credentials.json'")
        print(f"  7. Place it here: {CREDS_PATH}")
        print("\nThen run this script again.\n")
        return

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    print(f"\n✅  Auth successful. token.json saved to: {TOKEN_PATH}")
    print("You can now run all Google Drive / Slides / Docs scripts.\n")


if __name__ == "__main__":
    main()
