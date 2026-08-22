import os
import json
import sys
import urllib.parse
import webbrowser
import requests
from google_auth_oauthlib.flow import InstalledAppFlow

# Fix python path if run from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def exchange_code_for_tokens(flow, code: str, redirect_uri: str) -> dict:
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        return {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
    except Exception as e:
        print(f"[Notice] flow.fetch_token encountered {e}. Trying direct HTTP fallback...")
        client_info = flow.client_config
        token_uri = client_info.get("token_uri", "https://oauth2.googleapis.com/token")
        payload = {
            "code": code,
            "client_id": client_info["client_id"],
            "client_secret": client_info["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        if getattr(flow, "code_verifier", None):
            payload["code_verifier"] = flow.code_verifier

        resp = requests.post(token_uri, data=payload, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        return {
            "token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "token_uri": token_uri,
            "client_id": client_info["client_id"],
            "client_secret": client_info["client_secret"],
            "scopes": SCOPES
        }

def main():
    print(f"Reading client secrets from: {settings.youtube_client_secrets_file}")
    
    if not os.path.exists(settings.youtube_client_secrets_file):
        print(f"ERROR: Client secrets file not found at {settings.youtube_client_secrets_file}")
        print("Please download it from Google Cloud Console and place it there.")
        sys.exit(1)
        
    redirect_uri = "http://localhost:8080/"
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.youtube_client_secrets_file, 
        SCOPES,
        redirect_uri=redirect_uri
    )
    
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    
    print("\n" + "=" * 75)
    print("STEP 1: Open the authorization link below in your browser:")
    print("=" * 75)
    print(auth_url)
    print("=" * 75)
    
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("\nSTEP 2: Log in and click 'Allow' on your YouTube account.")
    print("STEP 3: Your browser will redirect to a page starting with 'http://localhost:8080/...'")
    print("        (If the browser says 'This site can't be reached', don't worry!)")
    print("STEP 4: Copy the ENTIRE URL from your browser's address bar and paste it below:\n")

    user_input = input("Paste redirected URL (or authorization code) here: ").strip()
    
    if not user_input:
        print("ERROR: Nothing was entered.")
        sys.exit(1)

    if "code=" in user_input:
        parsed = urllib.parse.urlparse(user_input)
        query_params = urllib.parse.parse_qs(parsed.query)
        code = query_params.get("code", [None])[0]
    else:
        code = user_input

    if not code:
        print("ERROR: Could not extract authorization code from input.")
        sys.exit(1)

    print("\nExchanging authorization code for OAuth tokens...")
    creds_data = exchange_code_for_tokens(flow, code=code, redirect_uri=redirect_uri)

    with open(settings.youtube_credentials_file, "w") as f:
        json.dump(creds_data, f, indent=4)
        
    print(f"\nSUCCESS! Credentials saved to {settings.youtube_credentials_file}")
    if creds_data.get("refresh_token"):
        print("✓ Refresh token successfully obtained!")
    else:
        print("[Warning] No refresh token found. You may need to run this again with prompt='consent'.")
    print("Keep this file secret. Do NOT commit it to Git.")
    print("For GitHub Actions, paste the contents of this file into the YOUTUBE_CREDENTIALS_JSON secret.")

if __name__ == "__main__":
    main()
