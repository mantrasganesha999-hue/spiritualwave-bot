import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
SECRETS = 'C:/SpiritualWave/client_secrets.json'
TOKEN = 'C:/SpiritualWave/token.pickle'

def autenticar():
    creds = None
    if os.path.exists(TOKEN):
        with open(TOKEN, 'rb') as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(SECRETS, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN, 'wb') as f:
            pickle.dump(creds, f)
    
    print("=== YOUTUBE AUTENTICADO OK ===")
    return creds

autenticar()