import requests, subprocess, os, random, base64, pickle, io, json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont

GROQ_KEY = os.environ.get('GROQ_API_KEY')
YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMAS_ES = [
    "mantra de Ganesha para atraer abundancia y eliminar deudas",
    "frecuencias 528hz para sanar el cuerpo y atraer prosperidad",
    "afirmaciones poderosas para manifestar dinero cada manana",
    "meditacion guiada para eliminar energia negativa y atraer exito",
    "ley de atraccion para atraer dinero abundancia y salud",
    "mantra poderoso de Ganesha para proteccion y abundancia",
    "musica de sanacion 432hz para dormir y restaurar el alma",
    "ganesha mantra om gan ganapataye namaha poder y abundancia",
    "528hz frecuencia milagro para sanar y atraer prosperidad",
    "mantra ganesha para el trabajo exito y prosperidad economica",
    "musica espiritual Ganesha para meditar y atraer paz interior",
    "frecuencias binaurales para activar la abundancia mientras duermes",
    "mantra poderoso para sanar el corazon y atraer amor divino",
    "musica tibetana cuencos para limpiar el aura y atraer paz",
    "afirmaciones de riqueza y exito para escuchar cada manana",
    "ganesha mantra para superar obstaculos y lograr tus metas",
    "frecuencias de sanacion para dormir profundo y despertar renovado",
    "meditacion de 10 minutos para activar la abundancia interior",
    "musica relajante de Ganesha para reducir el estres y ansiedad",
    "mantra de la prosperidad para atraer dinero en 21 dias",
]

TEMAS_EN = [
    "Ganesha mantra for abundance and removing obstacles 528hz",
    "Powerful Ganesha chant to attract money and prosperity",
    "432hz healing frequency Ganesha meditation deep sleep music",
    "Om Gan Ganapataye Namaha most powerful Ganesha mantra",
    "Ganesha divine frequency to remove all negative energy",
    "528hz miracle tone Ganesha blessing abundance wealth",
    "Ganesha mantra for success luck and divine protection",
    "Deep meditation music Ganesha 432hz sleep healing",
    "Ganesha frequency to attract love peace and abundance",
    "741hz cleansing frequency remove toxins and negative energy",
    "Ganesha powerful chant for financial abundance and success",
    "963hz frequency activate pineal gland spiritual awakening",
    "Ganesha morning mantra for positive energy and good luck",
    "852hz return to spiritual order Ganesha meditation music",
    "Tibetan singing bowls with Ganesha mantra deep healing",
    "Ganesha sleep music remove obstacles while you sleep 8 hours",
]

TEMAS_SHORTS_ES = [
    "Ganesha mantra para abundancia instantanea",
    "528hz frecuencia milagro activa ahora",
    "Om Gan Ganapataye Namaha poder infinito",
    "Mantra Ganesha elimina obstaculos hoy",
    "Activa tu abundancia con Ganesha ahora",
    "Ganesha te protege y bendice hoy",
    "Mantra sagrado para atraer dinero rapido",
    "Ganesha elimina toda energia negativa ahora",
    "Mantra de prosperidad Om Ganesha 528hz",
    "Frecuencia 432hz activa tu prosperidad ahora",
    "Ganesha te abre los caminos hacia el exito",
    "Escucha este mantra y cambia tu vida hoy",
    "528hz la frecuencia del milagro y la abundancia",
    "Ganesha blessing activa en 60 segundos",
]

TEMAS_SHORTS_EN = [
    "Ganesha abundance mantra 528hz miracle",
    "Remove obstacles Ganesha powerful chant now",
    "Divine Ganesha frequency activate abundance",
    "Om Gan Ganapataye Namaha infinite power",
    "Ganesha blessing money prosperity now",
    "528hz Ganesha miracle frequency activate",
    "Ganesha opens your path to success today",
    "Listen to this mantra and change your life",
    "432hz activate your prosperity right now",
    "Ganesha protection shield activate now",
]

EMOJIS_TITULO = ["🔱", "✨", "🙏", "⚡", "🌟", "💫", "🎯", "🔥", "💎", "🌙"]

def telegram(mensaje):
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT, 'text': mensaje, 'parse_mode': 'HTML'},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}")

def get_imagenes():
    folder = os.path.join(BASE, 'assets/backgrounds')
    imgs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.startswith('ganesha') and f.endswith('.jpg')
    ]
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
    texto = texto.replace('**', '').replace('__', '')
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

def generar_guion(tema, lang='es'):
    print(f"[1/4] Generando guion {lang}...")
    emoji = random.choice(EMOJIS_TITULO)
    if lang == 'es':
        prompt = f"""Eres experto en contenido espiritual de YouTube en espanol latino.
Genera contenido VIRAL para un video sobre: {tema}
Sin tildes ni caracteres especiales ni asteriscos ni markdown.
Responde EXACTAMENTE en este formato sin simbolos extra:
TITULO: {emoji} [titulo maximo 60 caracteres, impactante con numero o pregunta]
DESCRIPCION: [500 palabras con keywords espirituales, beneficios, instrucciones de uso, CTA para suscribirse a youtube.com/@SpiritualWave888]
TAGS: [30 hashtags separados por espacios]"""
    else:
        prompt = f"""You are a viral spiritual YouTube expert.
Generate content for: {tema}
No asterisks, no markdown, no special symbols.
Reply EXACTLY in this format:
TITULO: {emoji} [title maximum 60 characters, with number or question]
DESCRIPCION: [500 words with spiritual keywords, benefits, how to use, CTA to subscribe to youtube.com/@SpiritualWave888]
TAGS: [30 hashtags separated by spaces]"""

    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2000}
    )
    contenido = r.json()['choices'][0]['message']['content']

    titulo = extraer_campo(contenido, 'TITULO', 'DESCRIPCION') or f"{emoji} {tema[:55]}"
    titulo = limpiar_texto(titulo)
    if len(titulo) > 65:
        titulo = titulo[:65].strip()

    descripcion = extraer_campo(contenido, 'DESCRIPCION', 'TAGS') or f"Video sobre {tema}"
    descripcion = limpiar_texto(descripcion)

    tags = extraer_campo(contenido, 'TAGS') or "#Ganesha #Mantra #Espiritual #528hz #Abundancia"
    tags = limpiar_texto(tags)

    return titulo, descripcion, tags

def generar_thumbnail(titulo, variante=1):
    print(f"Generando thumbnail HD variante {variante}...")
    try:
        imagenes = get_imagenes()
        if not imagenes:
            return None

        img_path = imagenes[variante % len(imagenes)]
        img = Image.open(img_path).resize((1920, 1080)).convert('RGB')

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([(0, img.height-260), (img.width, img.height)], fill=(0, 0, 0, 190))
        d.rectangle([(0, 0), (img.width, 100)], fill=(0, 0, 0, 170))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        draw = ImageDraw.Draw(img)

        try:
            font_grande = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
            font_medio = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 42)
            font_pequeno = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
        except:
            font_grande = ImageFont.load_default()
            font_medio = ImageFont.load_default()
            font_pequeno = ImageFont.load_default()

        canal = 'SpiritualWave'
        bbox = draw.textbbox((0, 0), canal, font=font_medio)
        w = bbox[2] - bbox[0]
        draw.text(((img.width-w)//2+3, 32), canal, fill=(0, 0, 0), font=font_medio)
        draw.text(((img.width-w)//2, 30), canal, fill=(255, 215, 0), font=font_medio)

        sub = 'Mantras & Frecuencias Divinas'
        bbox = draw.textbbox((0, 0), sub, font=font_pequeno)
        w = bbox[2] - bbox[0]
        draw.text(((img.width-w)//2, 78), sub, fill=(200, 180, 100), font=font_pequeno)

        titulo_clean = limpiar_texto(titulo.replace('#Shorts', ''))[:50]
        palabras = titulo_clean.split()
        lineas = []
        linea = ""
        for p in palabras:
            test = linea + " " + p if linea else p
            bbox_test = draw.textbbox((0, 0), test, font=font_grande)
            if bbox_test[2] - bbox_test[0] < img.width - 100:
                linea = test
            else:
                if linea:
                    lineas.append(linea)
                linea = p
        if linea:
            lineas.append(linea)

        y = img.height - 250
        for linea in lineas[:3]:
            bbox = draw.textbbox((0, 0), linea, font=font_grande)
            w = bbox[2] - bbox[0]
            x = (img.width - w) // 2
            draw.text((x+4, y+4), linea, fill=(0, 0, 0), font=font_grande)
            draw.text((x, y), linea, fill=(255, 255, 255), font=font_grande)
            y += 88

        path = f'/tmp/thumbnail_{variante}.jpg'
        img.save(path, 'JPEG', quality=97)
        print(f"  Thumbnail HD OK")
        return path
    except Exception as e:
        print(f"  Thumbnail error: {e}")
        return None

def montar_video(titulo, duracion=3600, es_short=False):
    print(f"Montando {'SHORT' if es_short else 'VIDEO ' + str(duracion//60) + 'min'} HD...")
    imagenes = get_imagenes()
    musicas = get_musicas()

    if not imagenes or not musicas:
        print("ERROR: Faltan imagenes o musica")
        return None

    musica = random.choice(musicas)
    titulo_clean = limpiar_texto(titulo)[:45].replace("'","").replace('"','').replace(':','-').replace('#','')
    lista_path = '/tmp/lista_short.txt' if es_short else '/tmp/lista.txt'
    salida = '/tmp/short.mp4' if es_short else '/tmp/video_final.mp4'

    dur_img = 10 if es_short else 15
    repeticiones = 2 if es_short else max(1, duracion // (len(imagenes) * dur_img) + 1)

    with open(lista_path, 'w') as f:
        for _ in range(repeticiones):
            imgs = imagenes.copy()
            random.shuffle(imgs)
            for img in imgs:
                f.write(f"file '{img}'\n")
                f.write(f"duration {dur_img}\n")
        f.write(f"file '{imagenes[0]}'\n")

    if es_short:
        filtro = (
            "split=2[blur][img];"
            "[blur]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "boxblur=20:20[bg];"
            "[img]scale=1080:-1[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
            "format=yuv420p,"
            f"drawtext=text='{titulo_clean}':fontcolor=white:fontsize=42:"
            "x=(w-text_w)/2:y=h-160:"
            "shadowcolor=0x000000CC:shadowx=3:shadowy=3,"
            "drawtext=text='SpiritualWave':fontcolor=0xFFD700:fontsize=30:"
            "x=(w-text_w)/2:y=80:shadowcolor=black:shadowx=2:shadowy=2"
        )
        t = '58'
    else:
        filtro = (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
            "format=yuv420p,"
            f"drawtext=text='{titulo_clean}':fontcolor=white:fontsize=52:"
            "x=(w-text_w)/2:y=h-90:"
            "shadowcolor=0x000000CC:shadowx=3:shadowy=3,"
            "drawtext=text='SpiritualWave':fontcolor=0xFFD700:fontsize=28:"
            "x=(w-text_w)/2:y=25:shadowcolor=black:shadowx=2:shadowy=2"
        )
        t = str(duracion)

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0', '-i', lista_path,
        '-stream_loop', '-1', '-i', musica,
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
        '-t', t, '-vf', filtro,
        '-preset', 'fast', '-crf', '18',
        salida
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(salida):
        print(f"  OK HD: {os.path.getsize(salida)//1024//1024}MB")
        return salida
    print(f"  Error: {result.stderr[-300:]}")
    return None

def agregar_capitulos(descripcion, duracion_min):
    caps = "\n\nCAPITULOS:\n00:00 - Introduccion y bienvenida\n"
    paso = duracion_min // 5
    temas_caps = ["Mantra principal", "Meditacion profunda", "Afirmaciones de abundancia", "Cierre y bendicion"]
    for i, tema_cap in enumerate(temas_caps):
        mins = (i+1) * paso
        caps += f"{mins:02d}:00 - {tema_cap}\n"
    caps += f"\nSuscribete: youtube.com/@SpiritualWave888\n"
    caps += f"Activa la campana para no perderte nada\n"
    return descripcion + caps

def subir_youtube(video_path, titulo, descripcion, tags, es_short=False, duracion_min=60, variante=1):
    print(f"Subiendo {'SHORT' if es_short else 'VIDEO'} a YouTube...")
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    youtube = build('youtube', 'v3', credentials=creds)

    titulo_final = f"{titulo} #Shorts" if es_short else titulo
    desc_final = descripcion if es_short else agregar_capitulos(descripcion, duracion_min)

    body = {
        'snippet': {
            'title': titulo_final[:100],
            'description': desc_final[:4900],
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
    print(f"  SUBIDO: {url}")

    if not es_short:
        thumb = generar_thumbnail(titulo, variante)
        if thumb:
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumb, mimetype='image/jpeg')
                ).execute()
                print("  Thumbnail HD OK")
            except Exception as e:
                print(f"  Thumbnail error: {e}")

        try:
            duracion_seg = duracion_min * 60
            start_ms = str((duracion_seg - 20) * 1000)
            youtube.videoEndscreens().insert(
                videoId=video_id,
                body={
                    "elements": [
                        {
                            "type": "VIDEO",
                            "endgameElementStyle": {
                                "image": {},
                                "position": {"cornerPosition": "TOP_LEFT"}
                            },
                            "videoid": {"videoId": "recent"},
                            "startOffsetMs": start_ms,
                            "durationMs": "15000"
                        },
                        {
                            "type": "SUBSCRIBE",
                            "endgameElementStyle": {
                                "image": {},
                                "position": {"cornerPosition": "BOTTOM_RIGHT"}
                            },
                            "startOffsetMs": start_ms,
                            "durationMs": "15000"
                        }
                    ]
                }
            ).execute()
            print("  End screen OK")
        except Exception as e:
            print(f"  End screen error: {e}")

    return video_id, url

# MAIN
print("\n=== SPIRITUALWAVE AUTO PRODUCER HD ===")
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
resultados = []

telegram(f"🔱 <b>SpiritualWave Producer iniciado</b>\n📅 {fecha}\n⏳ Generando 4 videos HD...")

try:
    tema_es = random.choice(TEMAS_ES)
    print(f"\n[VIDEO ES] {tema_es}")
    titulo_es, desc_es, tags_es = generar_guion(tema_es, 'es')
    video_es = montar_video(titulo_es, duracion=3600)
    if video_es:
        vid_id, url = subir_youtube(video_es, titulo_es, desc_es, tags_es, duracion_min=60, variante=1)
        resultados.append({'tipo': 'VIDEO ES', 'titulo': titulo_es, 'url': url})
        telegram(f"✅ <b>Video ES subido</b>\n🎬 {titulo_es}\n🔗 {url}")

    tema_en = random.choice(TEMAS_EN)
    print(f"\n[VIDEO EN] {tema_en}")
    titulo_en, desc_en, tags_en = generar_guion(tema_en, 'en')
    video_en = montar_video(titulo_en, duracion=3600)
    if video_en:
        vid_id, url = subir_youtube(video_en, titulo_en, desc_en, tags_en, duracion_min=60, variante=2)
        resultados.append({'tipo': 'VIDEO EN', 'titulo': titulo_en, 'url': url})
        telegram(f"✅ <b>Video EN subido</b>\n🎬 {titulo_en}\n🔗 {url}")

    tema_short_es = random.choice(TEMAS_SHORTS_ES)
    print(f"\n[SHORT ES] {tema_short_es}")
    short_es = montar_video(tema_short_es, es_short=True)
    if short_es:
        vid_id, url = subir_youtube(short_es, tema_short_es, f"🙏 {tema_short_es}\n\nSuscribete: youtube.com/@SpiritualWave888\n\n#Ganesha #Shorts #Mantra #Espiritual #Abundancia #528hz", "#Ganesha #Shorts #Mantra #Espiritual #Abundancia #528hz #SpiritualWave", es_short=True)
        resultados.append({'tipo': 'SHORT ES', 'titulo': tema_short_es, 'url': url})
        telegram(f"✅ <b>Short ES subido</b>\n🎬 {tema_short_es}\n🔗 {url}")

    tema_short_en = random.choice(TEMAS_SHORTS_EN)
    print(f"\n[SHORT EN] {tema_short_en}")
    short_en = montar_video(tema_short_en, es_short=True)
    if short_en:
        vid_id, url = subir_youtube(short_en, tema_short_en, f"🙏 {tema_short_en}\n\nSubscribe: youtube.com/@SpiritualWave888\n\n#Ganesha #Shorts #Mantra #Spiritual #Abundance #528hz", "#Ganesha #Shorts #Mantra #Spiritual #Abundance #528hz #SpiritualWave", es_short=True)
        resultados.append({'tipo': 'SHORT EN', 'titulo': tema_short_en, 'url': url})
        telegram(f"✅ <b>Short EN subido</b>\n🎬 {tema_short_en}\n🔗 {url}")

    resumen = f"🔱 <b>Produccion HD completada</b>\n📅 {fecha}\n\n"
    for r in resultados:
        resumen += f"✅ {r['tipo']}: {r['titulo'][:40]}\n"
    resumen += f"\n📊 Total: {len(resultados)} videos HD subidos"
    telegram(resumen)

except Exception as e:
    telegram(f"❌ <b>ERROR</b>\n📅 {fecha}\n⚠️ {str(e)[:200]}")
    print(f"ERROR: {e}")
    raise