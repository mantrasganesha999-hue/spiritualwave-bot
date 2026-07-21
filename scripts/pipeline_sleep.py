import requests, subprocess, os, random, base64, pickle
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

GROQ_KEY = os.environ.get('GROQ_API_KEY')
YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMAS_SLEEP = [
    "8 Hours Ganesha Sleep Music 528hz Deep Healing While You Sleep",
    "8 Hours 432hz Ganesha Meditation Music Deep Sleep Relaxation",
    "8 Hours Tibetan Bowls Ganesha Sleep Music Remove Negative Energy",
    "8 Hours Ganesha Abundance Frequency Sleep Music Attract Money",
    "8 Hours 963hz Ganesha Deep Sleep Music Spiritual Awakening",
    "8 Hours Ganesha Healing Frequency Sleep Music Anxiety Relief",
    "8 Hours Om Mantra Ganesha Sleep Music Deep Relaxation",
    "8 Hours 528hz Miracle Tone Ganesha Sleep Music DNA Repair",
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

def get_imagenes():
    folder = os.path.join(BASE, 'assets/backgrounds')
    imgs = [os.path.join(folder, f) for f in os.listdir(folder) if f.startswith('ganesha') and f.endswith('.jpg')]
    random.shuffle(imgs)
    return imgs

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
            todas.append(p)
    return todas

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = texto.replace('*', '').replace('_', '').replace('`', '')
    texto = ' '.join(texto.split())
    return texto.strip()

def extraer_campo(contenido, campo, siguiente=None):
    try:
        if campo + ':' not in contenido:
            return None
        inicio = contenido.index(campo + ':') + len(campo) + 1
        if siguiente and siguiente + ':' in contenido:
            fin = contenido.index(siguiente + ':', inicio)
            return contenido[inicio:fin].strip()
        else:
            return contenido[inicio:].strip()
    except:
        return None

def generar_descripcion(titulo):
    prompt = f"""You are a viral spiritual YouTube expert.
Generate a description for a video titled: {titulo}
No asterisks, no markdown.
Reply EXACTLY in this format:
DESCRIPCION: [400 words with sleep music keywords, benefits of Ganesha frequencies, how to use, CTA to subscribe to youtube.com/@SpiritualWave888]
TAGS: [30 relevant hashtags separated by spaces about sleep music meditation Ganesha]"""

    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 1500}
    )
    contenido = r.json()['choices'][0]['message']['content']
    descripcion = extraer_campo(contenido, 'DESCRIPCION', 'TAGS') or f"Sleep music video: {titulo}"
    tags = extraer_campo(contenido, 'TAGS') or "#SleepMusic #Ganesha #528hz #Meditation #DeepSleep"
    return limpiar_texto(descripcion), limpiar_texto(tags)

def generar_thumbnail_sleep(titulo):
    print("Generando thumbnail sleep...")
    try:
        imagenes = get_imagenes()
        if not imagenes:
            return None
        img_path = random.choice(imagenes)
        img = Image.open(img_path).resize((1920, 1080)).convert('RGB')

        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.7)

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        for i in range(350):
            alpha = int(230 * (i / 350))
            d.rectangle([(0, img.height - 350 + i), (img.width, img.height - 349 + i)], fill=(10, 10, 40, alpha))
        d.rectangle([(0, 0), (img.width, 120)], fill=(10, 10, 40, 190))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        draw = ImageDraw.Draw(img)
        try:
            font_titulo = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 76)
            font_canal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 44)
        except:
            font_titulo = ImageFont.load_default()
            font_canal = ImageFont.load_default()

        canal = 'SpiritualWave'
        bbox = draw.textbbox((0, 0), canal, font=font_canal)
        w = bbox[2] - bbox[0]
        draw.text(((img.width-w)//2, 30), canal, fill=(150, 180, 255), font=font_canal)

        titulo_clean = "8 HOURS SLEEP MUSIC"
        bbox = draw.textbbox((0, 0), titulo_clean, font=font_titulo)
        w = bbox[2] - bbox[0]
        x = (img.width - w) // 2
        y = img.height - 260
        for dx, dy in [(-3,3),(3,3),(3,-3),(-3,-3)]:
            draw.text((x+dx, y+dy), titulo_clean, fill=(0, 0, 0), font=font_titulo)
        draw.text((x, y), titulo_clean, fill=(200, 220, 255), font=font_titulo)

        path = '/tmp/thumbnail_sleep.jpg'
        img.save(path, 'JPEG', quality=98)
        return path
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None

def montar_video_8h(titulo):
    print("Montando video de 8 horas...")
    imagenes = get_imagenes()
    musicas = get_musicas()
    if not imagenes or not musicas:
        return None

    musica = random.choice(musicas)
    duracion = 28800
    lista_path = '/tmp/lista_sleep.txt'
    salida = '/tmp/video_sleep.mp4'
    dur_img = 25
    repeticiones = max(1, duracion // (len(imagenes) * dur_img) + 1)

    with open(lista_path, 'w') as f:
        for _ in range(repeticiones):
            imgs = imagenes.copy()
            random.shuffle(imgs)
            for img in imgs:
                f.write(f"file '{img}'\n")
                f.write(f"duration {dur_img}\n")
        f.write(f"file '{imagenes[0]}'\n")

    filtro = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
        "format=yuv420p,"
        f"drawtext=text='SpiritualWave':fontcolor=0xFFD700:fontsize=28:"
        "x=(w-text_w)/2:y=25:shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', lista_path,
        '-stream_loop', '-1', '-i', musica,
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
        '-t', str(duracion), '-vf', filtro,
        '-preset', 'fast', '-crf', '20', salida
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(salida):
        print(f"OK: {os.path.getsize(salida)//1024//1024}MB")
        return salida
    print(f"Error: {result.stderr[-300:]}")
    return None

def subir_youtube_sleep(video_path, titulo, descripcion, tags):
    print("Subiendo video de 8 horas...")
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    youtube = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': titulo[:100],
            'description': descripcion[:4900],
            'tags': tags.split()[:30],
            'categoryId': '22'
        },
        'status': {'privacyStatus': 'public'}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response = youtube.videos().insert(
        part='snippet,status', body=body, media_body=media
    ).execute()
    video_id = response['id']
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"SUBIDO: {url}")

    thumb = generar_thumbnail_sleep(titulo)
    if thumb:
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb, mimetype='image/jpeg')).execute()
        except Exception as e:
            print(f"Thumbnail error: {e}")

    try:
        playlists = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
        playlist_id = None
        for pl in playlists.get('items', []):
            if pl['snippet']['title'] == 'Sleep Music':
                playlist_id = pl['id']
                break
        if not playlist_id:
            resp = youtube.playlists().insert(
                part='snippet,status',
                body={'snippet': {'title': 'Sleep Music', 'description': 'Ganesha Sleep Music - SpiritualWave'}, 'status': {'privacyStatus': 'public'}}
            ).execute()
            playlist_id = resp['id']
        youtube.playlistItems().insert(
            part='snippet',
            body={'snippet': {'playlistId': playlist_id, 'resourceId': {'kind': 'youtube#video', 'videoId': video_id}}}
        ).execute()
    except Exception as e:
        print(f"Playlist error: {e}")

    return video_id, url

# MAIN
print("=== SLEEP MUSIC PRODUCER ===")
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
telegram(f"🌙 <b>Sleep Music Producer iniciado</b>\n📅 {fecha}")

try:
    titulo = random.choice(TEMAS_SLEEP)
    descripcion, tags = generar_descripcion(titulo)
    video = montar_video_8h(titulo)
    if video:
        vid_id, url = subir_youtube_sleep(video, titulo, descripcion, tags)
        telegram(f"✅ <b>Video 8H Sleep subido</b>\n🎬 {titulo}\n🔗 {url}")
    else:
        telegram("❌ Error generando video de 8 horas")
except Exception as e:
    telegram(f"❌ <b>ERROR Sleep Music</b>\n⚠️ {str(e)[:200]}")
    raise