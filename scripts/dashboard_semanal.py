import requests, base64, pickle, os
from datetime import datetime, timedelta
from googleapiclient.discovery import build

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')

def telegram(msg):
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT, 'text': msg, 'parse_mode': 'HTML'},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}")

def get_youtube_service():
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    youtube = build('youtube', 'v3', credentials=creds)
    analytics = build('youtubeAnalytics', 'v2', credentials=creds)
    return youtube, analytics

def obtener_estadisticas_canal(youtube):
    try:
        response = youtube.channels().list(
            part='statistics,snippet',
            mine=True
        ).execute()
        canal = response['items'][0]
        stats = canal['statistics']
        return {
            'subs': int(stats.get('subscriberCount', 0)),
            'vistas_totales': int(stats.get('viewCount', 0)),
            'videos_totales': int(stats.get('videoCount', 0))
        }
    except Exception as e:
        print(f"Error stats canal: {e}")
        return None

def obtener_analytics_semana(analytics):
    try:
        fin = datetime.now().strftime('%Y-%m-%d')
        inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        response = analytics.reports().query(
            ids='channel==MINE',
            startDate=inicio,
            endDate=fin,
            metrics='views,estimatedMinutesWatched,subscribersGained,likes,comments',
            dimensions='day'
        ).execute()

        rows = response.get('rows', [])
        total_vistas = sum(row[1] for row in rows) if rows else 0
        total_minutos = sum(row[2] for row in rows) if rows else 0
        total_subs_ganados = sum(row[3] for row in rows) if rows else 0
        total_likes = sum(row[4] for row in rows) if rows else 0
        total_comentarios = sum(row[5] for row in rows) if rows else 0

        return {
            'vistas_semana': total_vistas,
            'horas_semana': round(total_minutos / 60, 1),
            'subs_ganados': total_subs_ganados,
            'likes': total_likes,
            'comentarios': total_comentarios
        }
    except Exception as e:
        print(f"Error analytics: {e}")
        return None

def obtener_top_video(analytics):
    try:
        fin = datetime.now().strftime('%Y-%m-%d')
        inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        response = analytics.reports().query(
            ids='channel==MINE',
            startDate=inicio,
            endDate=fin,
            metrics='views',
            dimensions='video',
            sort='-views',
            maxResults=1
        ).execute()

        rows = response.get('rows', [])
        if rows:
            return rows[0][0], rows[0][1]
        return None, 0
    except Exception as e:
        print(f"Error top video: {e}")
        return None, 0

def obtener_titulo_video(youtube, video_id):
    try:
        response = youtube.videos().list(part='snippet', id=video_id).execute()
        items = response.get('items', [])
        if items:
            return items[0]['snippet']['title']
        return "Desconocido"
    except:
        return "Desconocido"

# MAIN
print("=== DASHBOARD SEMANAL ===")

try:
    youtube, analytics = get_youtube_service()

    stats_canal = obtener_estadisticas_canal(youtube)
    stats_semana = obtener_analytics_semana(analytics)
    top_video_id, top_video_vistas = obtener_top_video(analytics)
    top_video_titulo = obtener_titulo_video(youtube, top_video_id) if top_video_id else "N/A"

    fecha = datetime.now().strftime("%Y-%m-%d")

    mensaje = f"📊 <b>DASHBOARD SEMANAL - SpiritualWave</b>\n📅 {fecha}\n\n"

    if stats_canal:
        mensaje += f"🔱 <b>Canal Total</b>\n"
        mensaje += f"👥 Suscriptores: {stats_canal['subs']}\n"
        mensaje += f"👁 Vistas totales: {stats_canal['vistas_totales']}\n"
        mensaje += f"🎬 Videos totales: {stats_canal['videos_totales']}\n\n"

    if stats_semana:
        mensaje += f"📈 <b>Esta Semana</b>\n"
        mensaje += f"👁 Vistas: {stats_semana['vistas_semana']}\n"
        mensaje += f"⏱ Horas vistas: {stats_semana['horas_semana']}\n"
        mensaje += f"➕ Subs ganados: {stats_semana['subs_ganados']}\n"
        mensaje += f"❤️ Likes: {stats_semana['likes']}\n"
        mensaje += f"💬 Comentarios: {stats_semana['comentarios']}\n\n"

    if top_video_id:
        mensaje += f"🏆 <b>Video mas visto esta semana</b>\n"
        mensaje += f"🎬 {top_video_titulo[:60]}\n"
        mensaje += f"👁 {top_video_vistas} vistas\n"
        mensaje += f"🔗 https://www.youtube.com/watch?v={top_video_id}\n"

    telegram(mensaje)
    print("Dashboard enviado OK")

except Exception as e:
    telegram(f"⚠️ Error generando dashboard semanal: {str(e)[:200]}")
    print(f"Error: {e}")