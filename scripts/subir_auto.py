import pickle, sys, os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN = 'C:/SpiritualWave/token.pickle'

num = sys.argv[1] if len(sys.argv) > 1 else '1'

video_path = f'C:/SpiritualWave/outputs/video_{num}.mp4'
meta_path = f'C:/SpiritualWave/outputs/metadata_{num}.txt'

if not os.path.exists(video_path):
    print(f"ERROR: No existe {video_path}")
    sys.exit(1)

with open(meta_path, 'r', encoding='utf-8') as f:
    meta = f.read()

titulo = meta.split('TITULO:')[1].split('\n')[0].strip()
descripcion = meta.split('DESCRIPCION:')[1].split('TAGS:')[0].strip()
tags = meta.split('TAGS:')[1].strip()

with open(TOKEN, 'rb') as f:
    creds = pickle.load(f)

youtube = build('youtube', 'v3', credentials=creds)

body = {
    'snippet': {
        'title': titulo,
        'description': descripcion,
        'tags': tags.split(),
        'categoryId': '22'
    },
    'status': {'privacyStatus': 'public'}
}

media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
response = youtube.videos().insert(
    part='snippet,status', body=body, media_body=media
).execute()

print(f"✅ Subido: https://www.youtube.com/watch?v={response['id']}")