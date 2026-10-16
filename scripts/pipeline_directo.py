"""SpiritualWave - 1 directo diario largo (~4 h).

Diseno para que sea estable en un runner de 2 vCPU:
  1. Se renderiza UNA VEZ un bucle de video (~3 min, 1080p30, transiciones suaves,
     texto fijo) ya codificado a bitrate de directo (4.5 Mbps, keyframe cada 2 s).
  2. Se renderiza una mezcla de audio de 1 h (en bucle) con las canciones de assets/music.
  3. Se transmite con `-c:v copy` (casi 0% CPU) repitiendo ambos en bucle.
Si la conexion RTMP cae, se reintenta hasta cubrir la duracion pedida.
"""
import os, sys, random, base64, pickle, time, subprocess, shutil, threading
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_cloud as pc  # helpers compartidos (xfade, mezcla de audio, miniaturas)

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
telegram = pc.telegram

W, H, FPS = 1920, 1080, 30
ENC_LIVE = ['-c:v', 'libx264', '-preset', 'veryfast',
            '-b:v', '4500k', '-maxrate', '4500k', '-bufsize', '9000k',
            '-g', '60', '-keyint_min', '60', '-sc_threshold', '0',
            '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', str(FPS)]

TEMAS_LIVE = [
    "Om Gan Ganapataye Namaha Live Chanting",
    "Ganesha Mantra for Peace and Abundance",
    "Live Ganesha Meditation Music for Deep Calm",
    "Ganpati Bappa Morya Devotional Live",
    "Ganesha Sleep Music Live to Remove Obstacles",
    "Powerful Ganesha Mantra for a Fresh Start",
    "528Hz Ganesha Frequency Music Live",
    "Vighnaharta Ganesha Mantras Live Stream",
    "Ganesha Morning Mantra for Positive Energy",
    "Ganesha Evening Prayer Music Live",
    "Shubh Labh Ganesha Mantra for Good Luck",
    "Ganesha Mantra for Focus and Clarity Live",
]


def datos_live():
    festival = pc.detectar_festival_hindu()
    if festival:
        tema = f"{festival} Special Ganesha Mantra Live"
    else:
        tema = TEMAS_LIVE[datetime.utcnow().timetuple().tm_yday % len(TEMAS_LIVE)]
    titulo = f"\U0001F534 LIVE: {tema} | SpiritualWave"
    descripcion = (
        f"{tema}\n\n"
        "Join this live stream of Ganesha mantras and devotional music. "
        "Relax, breathe and let the sacred sound of Om Gan Ganapataye Namaha fill your space.\n\n"
        "Subscribe: youtube.com/@SpiritualWave888\n\n"
        "#Ganesha #Mantra #Live #Meditation #GanpatiBappa #SpiritualWave\n\n"
        "The music, images and videos were created with artificial intelligence tools."
    )
    return tema, titulo[:100], descripcion


def construir_base(trabajo):
    """Bucle de video listo para transmitir con -c:v copy."""
    font = f"fontfile={pc.FUENTE_BOLD}:" if os.path.exists(pc.FUENTE_BOLD) else ""
    vf_post = (
        pc.GRADE_VIDEO +
        ",drawbox=x=40:y=28:w=150:h=58:color=0xD40000@0.95:t=fill"
        f",drawtext={font}text='LIVE':fontcolor=white:fontsize=38:x=72:y=38"
        f",drawtext={font}text='SpiritualWave':fontcolor=0xFFD700@0.9:fontsize=34:"
        "x=w-text_w-40:y=34:borderw=2:bordercolor=black@0.8"
        f",drawtext={font}text='Om Gan Ganapataye Namaha':fontcolor=0xFFD700:fontsize=52:"
        "x=(w-text_w)/2:y=h-110:borderw=3:bordercolor=black:shadowcolor=black:shadowx=3:shadowy=3"
    )
    segmentos = pc.construir_segmentos(False, W, H, FPS, trabajo, n_clips=40, por_segmento=8,
                                       vf_post=vf_post, enc=ENC_LIVE)
    if not segmentos:
        return None
    random.shuffle(segmentos)
    lista = f'{trabajo}/lista_base.txt'
    with open(lista, 'w') as f:
        for seg, _ in segmentos:
            f.write(f"file '{seg}'\n")
    base = f'{trabajo}/base_live.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
                        '-c', 'copy', base], capture_output=True, text=True)
    if os.path.exists(base) and os.path.getsize(base) > 100000:
        total = sum(d for _, d in segmentos)
        print(f"  Base de video OK: {total:.0f}s, {os.path.getsize(base)//1024//1024}MB")
        return base
    print(f"  Error uniendo base: {r.stderr[-300:]}")
    return None


def conectar_youtube():
    from google.auth.transport.requests import Request
    creds = pickle.loads(base64.b64decode(YOUTUBE_TOKEN_B64))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)


def miniatura_live(tema):
    path = pc.generar_thumbnail(tema, variante=random.randint(0, 9),
                                texto_marca='SpiritualWave',
                                subtexto='LIVE Ganesha Mantras')
    if not path:
        return None
    try:
        img = Image.open(path).convert('RGB')
        d = ImageDraw.Draw(img)
        fuente = ImageFont.truetype(pc.FUENTE_BOLD, 84)
        d.rounded_rectangle([60, 160, 400, 270], radius=20, fill=(212, 0, 0), outline=(255, 255, 255), width=4)
        d.text((100, 170), "LIVE", fill=(255, 255, 255), font=fuente)
        img.save(path, 'JPEG', quality=95)
    except Exception as e:
        print(f"  Badge LIVE error (se usa miniatura sin badge): {e}")
    return path


def obtener_stream(youtube):
    """Reutiliza un liveStream 1080p30 existente; si no hay, crea uno."""
    try:
        existentes = youtube.liveStreams().list(part='snippet,cdn', mine=True, maxResults=25).execute()
        for it in existentes.get('items', []):
            cdn = it.get('cdn', {})
            if cdn.get('resolution') in ('1080p', 'variable') and cdn.get('ingestionType') == 'rtmp':
                print("  Reutilizando stream existente")
                return it
    except Exception as e:
        print(f"  No se pudo listar streams: {e}")
    return youtube.liveStreams().insert(
        part="snippet,cdn",
        body={"snippet": {"title": "SpiritualWave Live Stream"},
              "cdn": {"frameRate": "30fps", "ingestionType": "rtmp", "resolution": "1080p"}}
    ).execute()


def crear_directo(youtube, tema, titulo, descripcion):
    inicio = (datetime.utcnow() + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    broadcast = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {"title": titulo, "description": descripcion, "scheduledStartTime": inicio},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
            "contentDetails": {"enableAutoStart": True, "enableAutoStop": True,
                               "recordFromStart": True, "enableDvr": True}
        }
    ).execute()
    broadcast_id = broadcast['id']
    stream = obtener_stream(youtube)
    youtube.liveBroadcasts().bind(part="id,contentDetails", id=broadcast_id, streamId=stream['id']).execute()
    ing = stream['cdn']['ingestionInfo']
    destino = f"{ing['ingestionAddress']}/{ing['streamName']}"

    thumb = miniatura_live(tema)
    if thumb:
        try:
            youtube.thumbnails().set(videoId=broadcast_id,
                                     media_body=MediaFileUpload(thumb, mimetype='image/jpeg')).execute()
            print("  Miniatura del directo OK")
        except Exception as e:
            print(f"  Miniatura del directo error (no critico): {e}")
    return broadcast_id, destino


def transmitir(base, audio, destino, duracion):
    inicio = time.time()
    fallos_tempranos = 0
    while True:
        restante = int(duracion - (time.time() - inicio))
        if restante < 60:
            break
        t0 = time.time()
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'warning',
               '-re', '-stream_loop', '-1', '-i', base,
               '-re', '-stream_loop', '-1', '-i', audio,
               '-map', '0:v', '-map', '1:a',
               '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-ar', '44100',
               '-t', str(restante), '-f', 'flv', destino]
        try:
            r = subprocess.run(cmd, timeout=restante + 180)
        except subprocess.TimeoutExpired:
            break
        if r.returncode == 0:
            break
        vivo = time.time() - t0
        print(f"  ffmpeg termino con codigo {r.returncode} tras {vivo:.0f}s; reintentando...")
        if vivo < 300:
            fallos_tempranos += 1
            if fallos_tempranos >= 5:
                raise RuntimeError("La transmision no se pudo mantener (5 fallos seguidos)")
        else:
            fallos_tempranos = 0
        time.sleep(15)


def verificar_en_vivo(youtube, broadcast_id):
    try:
        r = youtube.liveBroadcasts().list(part='status', id=broadcast_id).execute()
        estado = r['items'][0]['status']['lifeCycleStatus']
        if estado == 'live':
            telegram(f"\U0001F534 <b>EN VIVO</b>\n\U0001F517 https://www.youtube.com/watch?v={broadcast_id}")
        else:
            telegram(f"⚠️ El directo sigue en estado '{estado}' tras 3 min. Revisa YouTube Studio.\n"
                     f"https://www.youtube.com/watch?v={broadcast_id}")
    except Exception as e:
        print(f"  No se pudo verificar el estado: {e}")


def main():
    print("=== SPIRITUALWAVE DIRECTO ===")
    try:
        horas = float(os.environ.get('DIRECTO_HORAS') or 4)
    except ValueError:
        horas = 4.0
    duracion = int(max(0.25, min(horas, 5.0)) * 3600)
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    tema, titulo, descripcion = datos_live()
    telegram(f"\U0001F534 <b>Preparando directo</b> ({duracion/3600:.1f} h)\n\U0001F4C5 {fecha}\n\U0001F3AC {titulo}")

    trabajo = '/tmp/live_trabajo'
    shutil.rmtree(trabajo, ignore_errors=True)
    os.makedirs(trabajo, exist_ok=True)
    try:
        base = construir_base(trabajo)
        if not base:
            raise RuntimeError("No se pudo construir el video base del directo")
        audio = pc.crear_mezcla_audio(min(duracion, 3600), salida=f'{trabajo}/audio_live.m4a')
        if not audio:
            raise RuntimeError("No se pudo construir la mezcla de audio (revisa assets/music)")

        youtube = conectar_youtube()
        broadcast_id, destino = crear_directo(youtube, tema, titulo, descripcion)
        print(f"  Broadcast: https://www.youtube.com/watch?v={broadcast_id}")
        chequeo = threading.Timer(180, verificar_en_vivo, args=(youtube, broadcast_id))
        chequeo.daemon = True
        chequeo.start()

        transmitir(base, audio, destino, duracion)

        try:
            youtube.liveBroadcasts().transition(broadcastStatus='complete', id=broadcast_id, part='status').execute()
        except Exception:
            pass  # enableAutoStop ya lo cierra
        telegram(f"✅ <b>Directo finalizado</b>\n\U0001F517 https://www.youtube.com/watch?v={broadcast_id}")
        print("=== DIRECTO FINALIZADO ===")
    except Exception as e:
        print(f"ERROR en directo: {e}")
        telegram(f"⚠️ Error en directo: {str(e)[:250]}")
        sys.exit(1)
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)


if __name__ == '__main__':
    main()
