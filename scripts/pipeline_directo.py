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
import notificar

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')

W, H, FPS = 1920, 1080, 30
ENC_LIVE = ['-c:v', 'libx264', '-preset', 'veryfast',
            '-b:v', '4500k', '-maxrate', '4500k', '-bufsize', '9000k',
            '-g', '60', '-keyint_min', '60', '-sc_threshold', '0',
            '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', str(FPS)]

TEMAS_LIVE = [
    "Om Gan Ganapataye Namaha Live Chanting",
    "Ganesha Devotional Music Live for Peace",
    "Live Ganesha Meditation Music",
    "Ganpati Bappa Morya Devotional Live",
    "Ganesha Evening Prayer Music Live",
    "Ganesha Morning Devotional Music Live",
    "Vighnaharta Ganesha Mantras Live Stream",
    "Ganesha Mantra Music for Focus Live",
    "Shubh Ganesha Devotional Music Live",
    "Ganesha Bhajans Live for Daily Devotion",
    "Soft Ganesha Chanting Live for a Quiet Evening",
    "Ganesha Mantra Music Live for Calm and Gratitude",
]


HORA_LIVE_UTC = (15, 10)   # 10:10 am Colombia = 8:40 pm India


def datos_live(dias=0):
    """Tema, titulo y descripcion del directo de hoy (dias=0) o de otro dia (dias=1 -> manana)."""
    ref = datetime.utcnow() + timedelta(days=dias)
    festival = pc.detectar_festival_hindu(ref - timedelta(hours=5))
    if festival:
        tema = f"{festival} Special Ganesha Mantra Live"
    else:
        tema = TEMAS_LIVE[ref.timetuple().tm_yday % len(TEMAS_LIVE)]
    titulo = f"\U0001F534 LIVE: {tema} | SpiritualWave"
    descripcion = (
        f"{tema}\n\n"
        "Join this live stream of Ganesha mantras and devotional music. "
        "Relax, breathe and let the sacred sound of Om Gan Ganapataye Namaha fill your space.\n\n"
        "\U0001F514 Live every day at 15:10 UTC (8:40 PM India | 10:10 AM Colombia). "
        "Tap the reminder so you don't miss it, and tell us in the chat where you are watching from.\n\n"
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


def _hora(b):
    t = b['snippet'].get('scheduledStartTime')
    return pc._fecha_yt(t) if t else None


def _listar_pendientes(youtube, part):
    """Directos que aun no han empezado (created/ready/testing), TODAS las paginas.
    Antes se leia solo 'all' con maxResults=50 y los viejos quedaban fuera de esa primera pagina."""
    items, token = [], None
    while True:
        r = youtube.liveBroadcasts().list(part=part, broadcastStatus='upcoming',
                                          maxResults=50, pageToken=token).execute()
        items += r.get('items', [])
        token = r.get('nextPageToken')
        if not token:
            return items


def buscar_programado(youtube):
    """Directo de hoy ya programado de antemano (sin conectar, 'created', dentro de las proximas 14 h)."""
    try:
        items = _listar_pendientes(youtube, 'snippet,status,contentDetails')
        ahora = datetime.utcnow()
        cands = [b for b in items
                 if b['status']['lifeCycleStatus'] == 'created' and not b.get('contentDetails', {}).get('boundStreamId')
                 and _hora(b) and ahora - timedelta(hours=3) <= _hora(b) <= ahora + timedelta(hours=14)]
        return min(cands, key=_hora) if cands else None
    except Exception as e:
        print(f"  No se pudo buscar directo programado: {e}")
        return None


def limpiar_pendientes(youtube, conservar=None):
    """Borra directos viejos que quedaron en 'created/ready/testing' sin emitirse.
    Si quedan, YouTube enciende ESE (viejo, con otro titulo) en vez del de hoy, porque comparten la clave de
    transmision. Nunca toca uno en vivo, el que se va a reutilizar (conservar) ni uno programado para despues."""
    borrados = 0
    try:
        items = _listar_pendientes(youtube, 'id,snippet,status')
        ahora = datetime.utcnow()
        for b in items:
            if b['status']['lifeCycleStatus'] not in ('created', 'ready', 'testing') or b['id'] == conservar:
                continue
            if _hora(b) and _hora(b) > ahora + timedelta(hours=14):
                continue   # el de manana, programado de antemano
            try:
                youtube.liveBroadcasts().delete(id=b['id']).execute()
                borrados += 1
            except Exception as e:
                print(f"  No se pudo borrar el directo viejo {b['id']}: {e}")
    except Exception as e:
        print(f"  No se pudo revisar directos pendientes: {e}")
    if borrados:
        print(f"  Directos viejos sin emitir borrados: {borrados}")
    return borrados


def _insertar_broadcast(youtube, titulo, descripcion, inicio):
    return youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {"title": titulo, "description": descripcion,
                        "scheduledStartTime": inicio.strftime("%Y-%m-%dT%H:%M:%S.000Z")},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
            "contentDetails": {"enableAutoStart": True, "enableAutoStop": True,
                               "recordFromStart": True, "enableDvr": True}
        }
    ).execute()


def _poner_miniatura(youtube, broadcast_id, tema):
    thumb = miniatura_live(tema)
    if thumb:
        try:
            youtube.thumbnails().set(videoId=broadcast_id,
                                     media_body=MediaFileUpload(thumb, mimetype='image/jpeg')).execute()
            print("  Miniatura del directo OK")
        except Exception as e:
            print(f"  Miniatura del directo error (no critico): {e}")


def crear_directo(youtube, tema, titulo, descripcion):
    """Usa el directo ya programado de antemano si existe; si no, crea uno nuevo.
    Devuelve (broadcast_id, destino_rtmp, titulo_real)."""
    titulo, descripcion = pc.sin_hz(titulo), pc.sin_hz(descripcion)
    previo = buscar_programado(youtube)
    limpiar_pendientes(youtube, conservar=previo['id'] if previo else None)
    stream = obtener_stream(youtube)
    ing = stream['cdn']['ingestionInfo']
    destino = f"{ing['ingestionAddress']}/{ing['streamName']}"

    if previo:
        try:
            youtube.liveBroadcasts().bind(part="id,contentDetails", id=previo['id'], streamId=stream['id']).execute()
            print(f"  Usando el directo programado de antemano: {previo['id']}")
            tema_prev = previo['snippet']['title'].replace('\U0001F534 LIVE: ', '').replace(' | SpiritualWave', '')
            _poner_miniatura(youtube, previo['id'], tema_prev)   # no critico: garantiza miniatura propia
            return previo['id'], destino, previo['snippet']['title']
        except Exception as e:
            print(f"  No se pudo usar el programado ({e}); se crea uno nuevo")
            try:
                youtube.liveBroadcasts().delete(id=previo['id']).execute()
            except Exception:
                pass

    broadcast = _insertar_broadcast(youtube, titulo, descripcion, datetime.utcnow() + timedelta(minutes=2))
    broadcast_id = broadcast['id']
    youtube.liveBroadcasts().bind(part="id,contentDetails", id=broadcast_id, streamId=stream['id']).execute()
    _poner_miniatura(youtube, broadcast_id, tema)
    return broadcast_id, destino, titulo


def programar_siguiente(youtube):
    """Crea (sin conectar a la transmision) el directo de la proxima salida para que aparezca como
    'Proximo directo' con recordatorio ~24 h antes. Es idempotente (si ya existe uno para esa salida no
    crea otro), reintenta 3 veces y avisa por Telegram si no lo logra. Devuelve el id o None."""
    ultimo_error = None
    for intento in range(1, 4):
        try:
            ahora = datetime.utcnow()
            t = ahora.replace(hour=HORA_LIVE_UTC[0], minute=HORA_LIVE_UTC[1], second=0, microsecond=0)
            while t < ahora + timedelta(hours=6):
                t += timedelta(days=1)
            for b in _listar_pendientes(youtube, 'id,snippet,status'):
                h = _hora(b)
                if h and abs((h - t).total_seconds()) < 3 * 3600:
                    print(f"  Directo de manana ya programado: {b['id']}")
                    return b['id']
            dias = (t.date() - (ahora - timedelta(hours=5)).date()).days
            tema, titulo, desc = datos_live(max(1, dias))
            b = _insertar_broadcast(youtube, pc.sin_hz(titulo), pc.sin_hz(desc), t)
            _poner_miniatura(youtube, b['id'], tema)
            print(f"  Directo de manana programado: https://www.youtube.com/watch?v={b['id']} ({t:%d %H:%M} UTC)")
            try:
                notificar.mensaje('\U0001F4C5', 'DIRECTO DE MAÑANA PROGRAMADO',
                                  [f"\U0001F4CC <b>{notificar.esc(titulo)}</b>", f"\U0001F550 {t:%d/%m %H:%M} UTC"],
                                  silencioso=True)
            except Exception:
                pass
            return b['id']
        except Exception as e:
            ultimo_error = e
            print(f"  No se pudo programar el directo de manana (intento {intento}/3): {e}")
            time.sleep(20)
    try:
        notificar.mensaje('⚠️', 'NO SE PUDO PROGRAMAR EL DIRECTO DE MAÑANA',
                          [f"{notificar.esc(str(ultimo_error)[:300])}", "Mañana se crea uno normal a las 10:00."])
    except Exception:
        pass
    return None


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


def verificar_en_vivo(youtube, broadcast_id, titulo):
    """Mira hasta 10 min (cada 60 s) si YouTube ya lo marca 'live'; avisa solo si de verdad no arranco."""
    url = f"https://www.youtube.com/watch?v={broadcast_id}"
    estado = '?'
    for _ in range(10):
        try:
            r = youtube.liveBroadcasts().list(part='status', id=broadcast_id).execute()
            estado = r['items'][0]['status']['lifeCycleStatus']
            if estado == 'live':
                notificar.directo_en_vivo(titulo, url)
                return
        except Exception as e:
            print(f"  No se pudo verificar el estado: {e}")
        time.sleep(60)
    notificar.directo_sin_vivo(estado, url)


def progreso_horario(youtube, broadcast_id, inicio, total, parar):
    """Cada hora avisa (en silencio) cuanto lleva el directo y cuanta gente lo ve."""
    while not parar.wait(3600):
        espectadores = None
        try:
            r = youtube.videos().list(part='liveStreamingDetails', id=broadcast_id).execute()
            espectadores = r['items'][0]['liveStreamingDetails'].get('concurrentViewers')
        except Exception as e:
            print(f"  No se pudo leer espectadores: {e}")
        notificar.directo_progreso(time.time() - inicio, total, espectadores)


def directo_ya_hecho_hoy():
    """True si hoy (hora Colombia) ya hay un directo en vivo, preparandose o terminado.
    Los directos 'created' sin conectar (el de manana, programado de antemano) NO cuentan. Cuesta 1 unidad."""
    try:
        r = conectar_youtube().liveBroadcasts().list(
            part='snippet,status,contentDetails', broadcastStatus='all', maxResults=10).execute()
        ini = pc.inicio_dia_colombia()
        for b in r.get('items', []):
            est = b['status']['lifeCycleStatus']
            real = b['snippet'].get('actualStartTime')
            prog = b['snippet'].get('scheduledStartTime')
            empezo_hoy = bool(real) and pc._fecha_yt(real) >= ini
            en_curso = est in ('live', 'liveStarting', 'testing')
            conectado_hoy = (est == 'ready' and b.get('contentDetails', {}).get('boundStreamId')
                             and prog and pc._fecha_yt(prog) >= ini)
            if empezo_hoy or en_curso or conectado_hoy:
                print(f"  Ya hay un directo de hoy: {b['id']} ({est})")
                return True
    except Exception as e:
        print(f"  No se pudo revisar directos de hoy ({e}); se transmite normal")
    return False


def main():
    print("=== SPIRITUALWAVE DIRECTO ===")
    if (os.environ.get('FORZAR') or '').strip().lower() not in ('1', 'true', 'si') and directo_ya_hecho_hoy():
        print("Ya hubo un directo hoy: no se abre otro. Usa FORZAR para saltarlo.")
        return
    try:
        horas = float(os.environ.get('DIRECTO_HORAS') or 4)
    except ValueError:
        horas = 4.0
    duracion = int(max(0.25, min(horas, 5.0)) * 3600)
    tema, titulo, descripcion = datos_live()
    notificar.directo_preparando(titulo, duracion / 3600)

    trabajo = '/tmp/live_trabajo'
    shutil.rmtree(trabajo, ignore_errors=True)
    os.makedirs(trabajo, exist_ok=True)
    parar = threading.Event()
    try:
        base = construir_base(trabajo)
        if not base:
            raise RuntimeError("No se pudo construir el video base del directo")
        audio = pc.crear_mezcla_audio(min(duracion, 3600), salida=f'{trabajo}/audio_live.m4a')
        if not audio:
            raise RuntimeError("No se pudo construir la mezcla de audio (revisa assets/music)")

        youtube = conectar_youtube()
        broadcast_id, destino, titulo = crear_directo(youtube, tema, titulo, descripcion)
        url = f"https://www.youtube.com/watch?v={broadcast_id}"
        print(f"  Broadcast: {url}")
        inicio = time.time()
        chequeo = threading.Timer(120, verificar_en_vivo, args=(youtube, broadcast_id, titulo))
        chequeo.daemon = True
        chequeo.start()
        programar_siguiente(youtube)   # ya al arrancar: no depende de que el job llegue vivo hasta el final
        progreso = threading.Thread(target=progreso_horario, args=(youtube, broadcast_id, inicio, duracion, parar),
                                    daemon=True)
        progreso.start()

        transmitir(base, audio, destino, duracion)
        parar.set()

        try:
            youtube.liveBroadcasts().transition(broadcastStatus='complete', id=broadcast_id, part='status').execute()
        except Exception:
            pass  # enableAutoStop ya lo cierra
        programar_siguiente(youtube)   # el de manana queda como 'Proximo directo' con recordatorio
        notificar.directo_finalizado(titulo, url, time.time() - inicio)
        print("=== DIRECTO FINALIZADO ===")
    except Exception as e:
        print(f"ERROR en directo: {e}")
        notificar.error('Directo en vivo', e)
        sys.exit(1)
    finally:
        parar.set()
        shutil.rmtree(trabajo, ignore_errors=True)


if __name__ == '__main__':
    main()
