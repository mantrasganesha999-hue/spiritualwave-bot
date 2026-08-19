import requests, subprocess, os, random, base64, pickle
from datetime import datetime
from googleapiclient.discovery import build

YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def telegram(msg):
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT, 'text': msg, 'parse_mode': 'HTML'},
            timeout=10
        )
    except:
        pass

def get_imagenes():
    folder = os.path.join(BASE, 'assets/backgrounds')
    imgs = [os.path.join(folder, f) for f in os.listdir(folder) if f.startswith('ganesha') and f.endswith('.jpg')]
    random.shuffle(imgs)
    return imgs

def get_clips():
    folder = os.path.join(BASE, 'assets/videos_ganesha_horizontal')
    if os.path.exists(folder):
        clips = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.mp4')]
        if clips:
            random.shuffle(clips)
            return clips
    return []

def get_musicas():
    todas = []
    for i in range(1, 22):
        p = os.path.join(BASE, f'assets/music/suno_{i}.mp3')
        if os.path.exists(p):
            todas.append(p)
    for i in range(1, 4):
        p = os.path.join(BASE, f'assets/music/mezcla_{i}.mp3')
        if os.path.exists(p):
            todas.append(p)
    return todas

def montar_video_directo(duracion=6000):
    print(f"Montando video para directo {duracion//60}min...")
    clips = get_clips()
    imagenes = get_imagenes()
    musicas = get_musicas()
    if not musicas:
        return None

    musica = random.choice(musicas)
    lista_path = '/tmp/lista_directo.txt'
    salida = '/tmp/video_directo.mp4'

    if clips and len(clips) >= 3:
        clips_norm = []
        for idx, clip in enumerate(clips[:10]):
            norm = f'/tmp/dnorm_{idx}.mp4'
            cmd = ['ffmpeg', '-y', '-i', clip, '-vf', 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=25', '-an', '-t', '8', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', norm]
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(norm):
                clips_norm.append(norm)

        if clips_norm:
            with open(lista_path, 'w') as f:
                reps = max(1, duracion // (8 * len(clips_norm)) + 1)
                for _ in range(reps):
                    for c in clips_norm:
                        f.write(f"file '{c}'\n")
        else:
            clips = []

    if not clips:
        dur_img = 20
        with open(lista_path, 'w') as f:
            reps = max(1, duracion // (len(imagenes) * dur_img) + 1)
            for _ in range(reps):
                for img in imagenes:
                    f.write(f"file '{img}'\n")
                    f.write(f"duration {dur_img}\n")
            f.write(f"file '{imagenes[0]}'\n")

    filtro = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
        "format=yuv420p,"
        "drawtext=text='Ganesha 528Hz Live':fontcolor=white:fontsize=44:"
        "x=(w-text_w)/2:y=h-80:shadowcolor=black:shadowx=3:shadowy=3,"
        "drawtext=text='SpiritualWave LIVE':fontcolor=0xFFD700:fontsize=32:"
        "x=(w-text_w)/2:y=25:shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista_path,
           '-stream_loop', '-1', '-i', musica, '-map', '0:v', '-map', '1:a',
           '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
           '-t', str(duracion), '-vf', filtro, '-preset', 'fast', '-crf', '20', salida]
    subprocess.run(cmd, capture_output=True)

    if os.path.exists(salida):
        print(f"  OK: {os.path.getsize(salida)//1024//1024}MB")
        return salida
    return None

def crear_directo(video_path):
    print("Creando transmision en vivo...")
    from google.auth.transport.requests import Request
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    youtube = build('youtube', 'v3', credentials=creds)

    broadcast = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {
                "title": "🔱 Ganesha 528Hz Live - Musica Espiritual - SpiritualWave",
                "description": "Transmision en vivo de musica espiritual con mantras de Ganesha y frecuencias 528hz.\n\nSuscribete: youtube.com/@SpiritualWave888\n\n#Ganesha #Live #528hz #Meditacion",
                "scheduledStartTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
            "contentDetails": {"enableAutoStart": True, "enableAutoStop": True, "recordFromStart": True}
        }
    ).execute()
    broadcast_id = broadcast['id']

    stream = youtube.liveStreams().insert(
        part="snippet,cdn",
        body={"snippet": {"title": "SpiritualWave Live Stream"},
              "cdn": {"frameRate": "30fps", "ingestionType": "rtmp", "resolution": "1080p"}}
    ).execute()

    stream_key = stream['cdn']['ingestionInfo']['streamName']
    rtmp_url = stream['cdn']['ingestionInfo']['ingestionAddress']

    youtube.liveBroadcasts().bind(
        part="id,contentDetails", id=broadcast_id, streamId=stream['id']
    ).execute()

    print(f"  Transmitiendo: {rtmp_url}/{stream_key}")

    cmd = ['ffmpeg', '-re', '-i', video_path,
           '-c:v', 'libx264', '-preset', 'veryfast', '-maxrate', '3000k', '-bufsize', '6000k',
           '-pix_fmt', 'yuv420p', '-g', '60', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
           '-f', 'flv', f'{rtmp_url}/{stream_key}']
    subprocess.run(cmd, timeout=6100)
    return broadcast_id

# MAIN
print("=== SPIRITUALWAVE DIRECTO ===")
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
telegram(f"🔴 <b>Iniciando transmision en vivo</b>\n📅 {fecha}\n⏳ Duracion: ~1.5 horas")

try:
    video = montar_video_directo(duracion=6000)
    if video:
        broadcast_id = crear_directo(video)
        telegram(f"🔴 <b>Directo finalizado</b>\n🔗 https://www.youtube.com/watch?v={broadcast_id}")
    else:
        telegram("⚠️ Error generando video para directo")
except Exception as e:
    telegram(f"⚠️ Error en directo: {str(e)[:200]}")
    print(f"Error: {e}")