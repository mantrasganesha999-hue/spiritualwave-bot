import pickle
from googleapiclient.discovery import build

with open('C:/SpiritualWave/token.pickle', 'rb') as f:
    creds = pickle.load(f)

youtube = build('youtube', 'v3', credentials=creds)
r = youtube.channels().list(part='statistics', mine=True).execute()
stats = r['items'][0]['statistics']
print(f"Suscriptores: {stats['subscriberCount']}")
print(f"Vistas totales: {stats['viewCount']}")
print(f"Videos totales: {stats['videoCount']}")