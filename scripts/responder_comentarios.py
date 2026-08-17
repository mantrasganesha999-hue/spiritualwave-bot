import os, random, base64, pickle, requests
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')

RESPUESTAS_ES = [
    "Jai Ganesh! Que este mantra traiga abundancia y paz a tu vida 🔱🙏",
    "Om Gan Ganapataye Namaha! Ganesha elimina todos tus obstaculos hoy ✨🕉",
    "Gracias por tu fe! Que Ganesha te bendiga con prosperidad infinita 💫🙏",
    "Tu energia espiritual es poderosa. Sigue practicando este mantra diariamente 🔱",
    "Que las frecuencias sagradas sanen tu alma y atraigan milagros a tu vida 🌟",
    "Ganpati Bappa Morya! Suscribete para mas mantras poderosos cada dia 🔱✨",
    "Tu devocion llega al corazon de Ganesha. Que sus bendiciones sean tuyas hoy 🙏💎",
]

RESPUESTAS_EN = [
    "Jai Ganesh! May this mantra bring abundance and peace to your life 🔱🙏",
    "Om Gan Ganapataye Namaha! Ganesha removes all your obstacles today ✨🕉",
    "Thank you for your faith! May Ganesha bless you with infinite prosperity 💫🙏",
    "Your spiritual energy is powerful. Keep practicing this mantra daily 🔱",
    "May sacred frequencies heal your soul and attract miracles to your life 🌟",
    "Ganpati Bappa Morya! Subscribe for more powerful mantras every day 🔱✨",
    "Your devotion reaches Ganesha's heart. May his blessings be yours today 🙏💎",
]

def telegram(msg):
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT, 'text': msg, 'parse_mode': 'HTML'},
            timeout=10
        )
    except:
        pass

def get_youtube():
    from google.auth.transport.requests import Request
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)

def responder_comentarios():
    print("=== RESPONDIENDO COMENTARIOS ===")
    youtube = get_youtube()
    respondidos = 0
    errores = 0

    try:
        videos = youtube.search().list(
            part='id',
            forMine=True,
            type='video',
            order='date',
            maxResults=10
        ).execute()

        video_ids = [item['id']['videoId'] for item in videos.get('items', [])]
        print(f"Revisando {len(video_ids)} videos recientes...")

        for video_id in video_ids:
            try:
                comentarios = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    order='time',
                    maxResults=5,
                    moderationStatus='published'
                ).execute()

                for item in comentarios.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    texto = snippet.get('textDisplay', '').lower()
                    autor = snippet.get('authorDisplayName', '')
                    comentario_id = item['id']
                    ya_respondido = item['snippet'].get('totalReplyCount', 0) > 0

                    if ya_respondido:
                        continue

                    palabras_positivas = ['gracias', 'beautiful', 'amazing', 'om', 'jai', 'ganesha',
                                        'mantra', 'blessings', 'love', 'peace', 'thank', 'wonderful',
                                        'bendicion', 'paz', 'amor', 'hermoso', 'poderoso', 'shantidev']

                    es_positivo = any(p in texto for p in palabras_positivas)

                    if not es_positivo and len(texto) < 5:
                        continue

                    es_ingles = any(w in texto for w in ['the', 'you', 'thank', 'beautiful', 'amazing', 'love', 'peace', 'bless'])
                    respuesta = random.choice(RESPUESTAS_EN if es_ingles else RESPUESTAS_ES)

                    try:
                        youtube.comments().insert(
                            part='snippet',
                            body={
                                'snippet': {
                                    'parentId': comentario_id,
                                    'textOriginal': respuesta
                                }
                            }
                        ).execute()
                        print(f"  Respondido a {autor}: {respuesta[:50]}...")
                        respondidos += 1
                    except Exception as e:
                        print(f"  Error respondiendo: {e}")
                        errores += 1

            except Exception as e:
                print(f"  Error en video {video_id}: {e}")

    except Exception as e:
        print(f"Error general: {e}")
        telegram(f"❌ Error en responder comentarios: {str(e)[:150]}")
        return

    msg = f"💬 <b>Comentarios respondidos</b>\n✅ Respondidos: {respondidos}\n❌ Errores: {errores}"
    telegram(msg)
    print(f"Listo: {respondidos} respondidos, {errores} errores")

responder_comentarios()