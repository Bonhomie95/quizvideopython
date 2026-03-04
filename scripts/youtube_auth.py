from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=SCOPES,
)

creds = flow.run_local_server(port=8080)

print("\n==== SAVE THIS REFRESH TOKEN ====\n")
print(creds.refresh_token)
