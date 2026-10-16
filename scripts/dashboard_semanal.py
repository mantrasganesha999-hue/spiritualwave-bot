import requests, base64, pickle, os, json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import notificar

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORIAL_PATH = os.path.join(BASE, 'historial_dashboard.json')

def get_youtube_service():
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    youtube = build('youtube', 'v3', credentials=creds)
    analytics = build('youtubeAnalytics', 'v2', credentials=creds)
    return youtube, analytics

def obtener_estadisticas_canal(youtube):
    try:
        response = youtube.channels().list(part='statistics,snippet', mine=True).execute()
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
            ids='channel==MINE', startDate=inicio, endDate=fin,
            metrics='views,estimatedMinutesWatched,subscribersGained,likes,comments',
            dimensions='day'
        ).execute()
        rows = response.get('rows', [])
        return {
            'vistas_semana': sum(row[1] for row in rows) if rows else 0,
            'horas_semana': round(sum(row[2] for row in rows) / 60, 1) if rows else 0,
            'subs_ganados': sum(row[3] for row in rows) if rows else 0,
            'likes': sum(row[4] for row in rows) if rows else 0,
            'comentarios': sum(row[5] for row in rows) if rows else 0
        }
    except Exception as e:
        print(f"Error analytics: {e}")
        return None

def obtener_top_video(analytics):
    try:
        fin = datetime.now().strftime('%Y-%m-%d')
        inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        response = analytics.reports().query(
            ids='channel==MINE', startDate=inicio, endDate=fin,
            metrics='views', dimensions='video', sort='-views', maxResults=1
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

def cargar_historial():
    try:
        with open(HISTORIAL_PATH, 'r') as f:
            return json.load(f)
    except:
        return []

def guardar_historial(historial):
    try:
        with open(HISTORIAL_PATH, 'w') as f:
            json.dump(historial, f, indent=2)
    except Exception as e:
        print(f"Error guardando historial: {e}")

def formatear_comparativa(actual, anterior, nombre, es_decimal=False):
    if anterior is None:
        return f"{actual}"
    diff = actual - anterior
    if diff > 0:
        flecha = "📈"
        signo = "+"
    elif diff < 0:
        flecha = "📉"
        signo = ""
    else:
        flecha = "➡️"
        signo = ""
    if es_decimal:
        return f"{actual} ({flecha} {signo}{diff:.1f})"
    return f"{actual} ({flecha} {signo}{diff})"

# MAIN
print("=== DASHBOARD SEMANAL ===")

try:
    youtube, analytics = get_youtube_service()

    stats_canal = obtener_estadisticas_canal(youtube)
    stats_semana = obtener_analytics_semana(analytics)
    top_video_id, top_video_vistas = obtener_top_video(analytics)
    top_video_titulo = obtener_titulo_video(youtube, top_video_id) if top_video_id else "N/A"

    fecha = datetime.now().strftime("%Y-%m-%d")

    historial = cargar_historial()
    semana_anterior = historial[-1] if historial else None

    lineas = []

    if stats_canal:
        subs_ant = semana_anterior['subs_total'] if semana_anterior else None
        vistas_ant = semana_anterior['vistas_totales'] if semana_anterior else None
        lineas += ["🔱 <b>Canal (total)</b>",
                   f"👥 Suscriptores: {formatear_comparativa(stats_canal['subs'], subs_ant, 'subs')}",
                   f"👁 Vistas totales: {formatear_comparativa(stats_canal['vistas_totales'], vistas_ant, 'vistas')}",
                   f"🎬 Videos publicados: {stats_canal['videos_totales']}", ""]

    if stats_semana:
        vistas_sem_ant = semana_anterior['vistas_semana'] if semana_anterior else None
        horas_sem_ant = semana_anterior['horas_semana'] if semana_anterior else None
        subs_gan_ant = semana_anterior['subs_ganados'] if semana_anterior else None
        likes_ant = semana_anterior['likes'] if semana_anterior else None
        comentarios_ant = semana_anterior['comentarios'] if semana_anterior else None
        lineas += ["📈 <b>Esta semana vs la anterior</b>",
                   f"👁 Vistas: {formatear_comparativa(stats_semana['vistas_semana'], vistas_sem_ant, 'vistas')}",
                   f"⏱ Horas vistas: {formatear_comparativa(stats_semana['horas_semana'], horas_sem_ant, 'horas', es_decimal=True)}",
                   f"➕ Suscriptores ganados: {formatear_comparativa(stats_semana['subs_ganados'], subs_gan_ant, 'subs')}",
                   f"❤️ Likes: {formatear_comparativa(stats_semana['likes'], likes_ant, 'likes')}",
                   f"💬 Comentarios: {formatear_comparativa(stats_semana['comentarios'], comentarios_ant, 'comentarios')}", ""]

    botones = []
    if top_video_id:
        lineas += ["🏆 <b>Video más visto de la semana</b>",
                   f"🎬 {notificar.esc(top_video_titulo[:70])}",
                   f"👁 {top_video_vistas} vistas"]
        botones.append(('▶️ Ver el video', f"https://www.youtube.com/watch?v={top_video_id}"))
    if lineas and lineas[-1] == "":
        lineas.pop()

    notificar.mensaje('📊', f'DASHBOARD SEMANAL · {fecha}', lineas, botones=botones)
    print("Dashboard enviado OK")

    nuevo_registro = {
        'fecha': fecha,
        'subs_total': stats_canal['subs'] if stats_canal else 0,
        'vistas_totales': stats_canal['vistas_totales'] if stats_canal else 0,
        'vistas_semana': stats_semana['vistas_semana'] if stats_semana else 0,
        'horas_semana': stats_semana['horas_semana'] if stats_semana else 0,
        'subs_ganados': stats_semana['subs_ganados'] if stats_semana else 0,
        'likes': stats_semana['likes'] if stats_semana else 0,
        'comentarios': stats_semana['comentarios'] if stats_semana else 0
    }
    historial.append(nuevo_registro)
    historial = historial[-12:]
    guardar_historial(historial)
    print("Historial actualizado OK")

except Exception as e:
    notificar.error('Dashboard semanal', e)
    print(f"Error: {e}")