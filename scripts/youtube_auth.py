import os
import json
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

# Fix python path if run from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    print(f"Reading client secrets from: {settings.youtube_client_secrets_file}")
    
    if not os.path.exists(settings.youtube_client_secrets_file):
        print(f"ERROR: Client secrets file not found at {settings.youtube_client_secrets_file}")
        print("Please download it from Google Cloud Console and place it there.")
        sys.exit(1)
        
    flow = InstalledAppFlow.from_client_secrets_file(settings.youtube_client_secrets_file, SCOPES)
    
    # Run local server to catch the redirect and generate tokens
    creds = flow.run_local_server(port=0)
    
    creds_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    
    with open(settings.youtube_credentials_file, "w") as f:
        json.dump(creds_data, f, indent=4)
        
    print(f"\nSUCCESS! Credentials saved to {settings.youtube_credentials_file}")
    print("Keep this file secret. Do NOT commit it to Git.")
    print("For GitHub Actions, you can set these values as Secrets.")

if __name__ == "__main__":
    main()
