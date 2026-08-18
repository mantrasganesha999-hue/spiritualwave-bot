import os, random, base64, pickle, requests
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')

POSTS_ES = [
    "🔱 Buenos dias! Que mantra de Ganesha escuchas hoy para atraer abundancia? Cuentanos abajo 🙏✨",
    "💫 PREGUNTA DEL DIA: Si Ganesha te concediera UN deseo hoy, cual seria? Escribelo en los comentarios 🕉🔱",
    "🌟 Tip espiritual: Repite 108 veces OM GAN GANAPATAYE NAMAHA antes de dormir y observa los cambios en tu vida 🙏",
    "⚡ Cual es tu frecuencia favorita para meditar? 528hz, 432hz o 963hz? Vota en los comentarios 🎵✨",
    "🔥 El secreto de Ganesha: La abundancia llega cuando dejas de pedir y empiezas a agradecer. Comparte si lo crees 🙏🌸",
    "💎 RETO 21 DIAS: Escucha un mantra de Ganesha cada manana por 21 dias y cuentanos los cambios. Quien se une? 🔱",
    "🌙 Antes de dormir: Pon un mantra de Ganesha y duerme con su energia protectora. Tu subconsciente manifestara mientras duermes ✨",
    "🕉 Dato sagrado: El numero 108 es sagrado en el hinduismo. Por eso repetimos los mantras 108 veces. Sabias esto? 🔱",
    "🙏 Comparte este canal con alguien que necesite paz y abundancia hoy. Tu gesto puede cambiar su vida 💫",
    "⚡ ENCUESTA: Como te sientes despues de escuchar mantras de Ganesha? 1) Con mas energia 2) En paz 3) Con esperanza 🔱",
]

POSTS_EN = [
    "🔱 Good morning! Which Ganesha mantra are you listening to today to attract abundance? Tell us below 🙏✨",
    "💫 QUESTION OF THE DAY: If Ganesha granted you ONE wish today, what would it be? Write it in the comments 🕉🔱",
    "🌟 Spiritual tip: Repeat OM GAN GANAPATAYE NAMAHA 108 times before sleeping and observe the changes in your life 🙏",
    "⚡ What is your favorite frequency for meditation? 528hz, 432hz or 963hz? Vote in the comments 🎵✨",
    "🔥 Ganesha's secret: Abundance comes when you stop asking and start being grateful. Share if you believe this 🙏🌸",
    "💎 21 DAY CHALLENGE: Listen to a Ganesha mantra every morning for 21 days and tell us the changes. Who joins? 🔱",
    "🌙 Before sleeping: Play a Ganesha mantra and sleep with his protective energy. Your subconscious will manifest while you sleep ✨",
    "🕉 Sacred fact: The number 108 is sacred in Hinduism. That is why we repeat mantras 108 times. Did you know this? 🔱",
    "🙏 Share this channel with someone who needs peace and abundance today. Your gesture can change their life 💫",
    "⚡ POLL: How do you feel after listening to Ganesha mantras? 1) More energy 2) At peace 3) Hopeful 🔱",
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
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)

def publicar_post():
    print("=== PUBLICANDO POST DE COMUNIDAD ===")
    youtube = get_youtube()

    hora = datetime.now().hour
    es_ingles = hora % 2 == 0

    post = random.choice(POSTS_EN if es_ingles else POSTS_ES)

    try:
        youtube.communityPosts().insert(
            part='snippet',
            body={
                'snippet': {
                    'type': 'textPost',
                    'textOriginal': post
                }
            }
        ).execute()
        print(f"Post publicado: {post[:60]}...")
        telegram(f"📢 <b>Post de Comunidad publicado</b>\n{post[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
        telegram(f"⚠️ Error en post comunidad: {str(e)[:150]}")

publicar_post()