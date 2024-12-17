import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    """Get credentials from the file or create new credentials."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    # It is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh the credentials if expired
        else:
            # If no valid credentials exist, run the OAuth2 flow to get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                'app/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_gmail_service():
    """Returns a Gmail API service."""
    creds = get_credentials()  # Get the credentials (either from file or by logging in)
    service = build('gmail', 'v1', credentials=creds)  # Build the Gmail service
    return service
