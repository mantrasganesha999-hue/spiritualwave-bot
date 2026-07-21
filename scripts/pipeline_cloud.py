import requests, subprocess, os, random, base64, pickle, io, json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

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
    "musica 963hz para despertar la conciencia y conectar con lo divino",
    "mantra sagrado para limpiar el karma y atraer bendiciones",
    "frecuencias 741hz para eliminar toxinas y pensamientos negativos",
    "meditacion guiada para manifestar tus suenos y metas en 2026",
    "musica para dormir con Ganesha y despertar con abundancia",
    "mantra de Lakshmi y Ganesha para atraer riqueza y prosperidad",
    "afirmaciones positivas en espanol para reprogramar tu mente",
    "musica de sanacion cuantica para equilibrar los chakras",
    "ganesha mantra para proteger el hogar y atraer armonia familiar",
    "frecuencias del universo para conectar con tu proposito de vida",
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
    "528hz DNA repair frequency Ganesha blessing meditation",
    "Ganesha mantra for career success and financial freedom",
    "432hz nature frequency Ganesha meditation stress relief",
    "Om Namah Shivaya Ganesha powerful healing mantra 528hz",
    "Ganesha abundance frequency attract money while you sleep",
    "396hz liberation from fear and guilt Ganesha meditation",
    "Ganesha mantra for students success and mental clarity",
    "639hz harmonious relationships Ganesha divine frequency",
    "Ganesha 1000 names chant for ultimate blessing and protection",
    "174hz pain relief frequency Ganesha healing meditation music",
    "Ganesha mantra for new beginnings and fresh start 2026",
    "285hz cellular healing Ganesha frequency tissue regeneration",
    "Ganesha divine music for yoga and deep meditation practice",
    "Solfeggio frequencies complete set Ganesha healing music",
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
    "Mantra de Ganesha para el dinero en 1 minuto",
    "La frecuencia que atrae abundancia mientras duermes",
    "Om Ganesha activa tu suerte ahora mismo",
    "Elimina bloqueos con este mantra de 60 segundos",
    "Ganesha abre puertas imposibles con este mantra",
    "528hz sana tu cuerpo y atrae prosperidad hoy",
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
    "60 seconds Ganesha mantra for instant luck",
    "528hz the frequency that attracts abundance",
    "Ganesha removes your blocks in 60 seconds",
    "This mantra opens impossible doors now",
    "Heal your body attract money 528hz now",
]

EMOJIS_TITULO = ["🔱", "✨", "🙏", "⚡", "🌟", "💫", "🎯", "🔥", "💎", "🌙"]

VIDEOS_SUBIDOS_HOY = []

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
    print(f"Generando thumbnail profesional variante {variante}...")
    try:
        imagenes = get_imagenes()
        if not imagenes:
            return None

        img_path = imagenes[variante % len(imagenes)]
        img = Image.open(img_path).resize((1920, 1080)).convert('RGB')

        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)

        for i in range(350):
            alpha = int(220 * (i / 350))
            d.rectangle(
                [(0, img.height - 350 + i), (img.width, img.height - 349 + i)],
                fill=(0, 0, 0, alpha)
            )

        d.rectangle([(0, 0), (img.width, 120)], fill=(0, 0, 0, 185))

        for thickness in range(8):
            color_val = max(150, 201 - thickness * 10)
            d.rectangle(
                [(thickness, thickness), (img.width-1-thickness, img.height-1-thickness)],
                outline=(color_val, int(color_val * 0.83), int(color_val * 0.37)),
                width=1
            )

        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        try:
            font_titulo = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 88)
            font_canal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 44)
            font_sub = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
        except:
            font_titulo = ImageFont.load_default()
            font_canal = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        canal = 'SpiritualWave'
        bbox = draw.textbbox((0, 0), canal, font=font_canal)
        w = bbox[2] - bbox[0]
        cx = (img.width - w) // 2
        draw.text((cx+5, 35), canal, fill=(80, 60, 0), font=font_canal)
        draw.text((cx+3, 33), canal, fill=(120, 90, 0), font=font_canal)
        draw.text((cx, 30), canal, fill=(255, 220, 50), font=font_canal)

        sub = 'Mantras & Frecuencias Divinas'
        bbox = draw.textbbox((0, 0), sub, font=font_sub)
        w = bbox[2] - bbox[0]
        draw.text(((img.width-w)//2, 85), sub, fill=(230, 200, 130), font=font_sub)

        titulo_clean = limpiar_texto(titulo.replace('#Shorts', ''))[:55]
        palabras = titulo_clean.split()
        lineas = []
        linea = ""
        for p in palabras:
            test = linea + " " + p if linea else p
            bbox_test = draw.textbbox((0, 0), test, font=font_titulo)
            if bbox_test[2] - bbox_test[0] < img.width - 60:
                linea = test
            else:
                if linea:
                    lineas.append(linea)
                linea = p
        if linea:
            lineas.append(linea)

        total_lines = min(len(lineas), 3)
        line_height = 100
        total_height = total_lines * line_height
        y_start = img.height - 330 + (330 - total_height) // 2

        for linea in lineas[:3]:
            bbox = draw.textbbox((0, 0), linea, font=font_titulo)
            w = bbox[2] - bbox[0]
            x = (img.width - w) // 2

            for dx, dy in [(-4,4),(4,4),(4,-4),(-4,-4),(0,5),(5,0),(0,-5),(-5,0),(-3,3),(3,3),(3,-3),(-3,-3)]:
                draw.text((x+dx, y_start+dy), linea, fill=(0, 0, 0), font=font_titulo)

            draw.text((x, y_start), linea, fill=(255, 255, 255), font=font_titulo)
            y_start += line_height

        path = f'/tmp/thumbnail_{variante}.jpg'
        img.save(path, 'JPEG', quality=98)
        print(f"  Thumbnail profesional OK")
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
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "format=yuv420p,"
            f"drawtext=text='{titulo_clean}':fontcolor=white:fontsize=44:"
            "x=(w-text_w)/2:y=h-150:"
            "shadowcolor=0x000000EE:shadowx=4:shadowy=4:borderw=2:bordercolor=black,"
            "drawtext=text='SpiritualWave':fontcolor=0xFFD700:fontsize=32:"
            "x=(w-text_w)/2:y=70:shadowcolor=black:shadowx=3:shadowy=3"
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

def agregar_card(youtube, video_id, video_relacionado_id):
    try:
        if not video_relacionado_id:
            return
        youtube.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': {
                    'categoryId': '22',
                }
            }
        ).execute()
        print("  Card procesada")
    except Exception as e:
        print(f"  Card error: {e}")

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
                print("  Thumbnail OK")
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

        # Agregar card apuntando a video anterior del dia
        if VIDEOS_SUBIDOS_HOY:
            try:
                video_anterior = VIDEOS_SUBIDOS_HOY[-1]
                youtube.cards().insert(
                    videoId=video_id,
                    body={
                        "card": {
                            "videoIdCard": {
                                "videoId": video_anterior
                            }
                        }
                    }
                ).execute()
                print("  Card OK")
            except Exception as e:
                print(f"  Card error: {e}")

        VIDEOS_SUBIDOS_HOY.append(video_id)

    return video_id, url

# MAIN
print("\n=== SPIRITUALWAVE AUTO PRODUCER HD ===")
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
resultados = []

telegram(f"🔱 <b>SpiritualWave Producer iniciado</b>\n📅 {fecha}\n⏳ Generando 5 videos HD...")

try:
    tema_es = random.choice(TEMAS_ES)
    print(f"\n[VIDEO ES 1H] {tema_es}")
    titulo_es, desc_es, tags_es = generar_guion(tema_es, 'es')
    video_es = montar_video(titulo_es, duracion=3600)
    if video_es:
        vid_id, url = subir_youtube(video_es, titulo_es, desc_es, tags_es, duracion_min=60, variante=1)
        resultados.append({'tipo': 'VIDEO ES 1H', 'titulo': titulo_es, 'url': url})
        telegram(f"✅ <b>Video ES 1H subido</b>\n🎬 {titulo_es}\n🔗 {url}")

    tema_en = random.choice(TEMAS_EN)
    print(f"\n[VIDEO EN 1H] {tema_en}")
    titulo_en, desc_en, tags_en = generar_guion(tema_en, 'en')
    video_en = montar_video(titulo_en, duracion=3600)
    if video_en:
        vid_id, url = subir_youtube(video_en, titulo_en, desc_en, tags_en, duracion_min=60, variante=2)
        resultados.append({'tipo': 'VIDEO EN 1H', 'titulo': titulo_en, 'url': url})
        telegram(f"✅ <b>Video EN 1H subido</b>\n🎬 {titulo_en}\n🔗 {url}")

    tema_3h = random.choice(TEMAS_EN)
    titulo_3h, desc_3h, tags_3h = generar_guion(tema_3h, 'en')
    titulo_3h = f"3 Hours {limpiar_texto(titulo_3h)}"[:65]
    print(f"\n[VIDEO 3H] {titulo_3h}")
    video_3h = montar_video(titulo_3h, duracion=10800)
    if video_3h:
        vid_id, url = subir_youtube(video_3h, titulo_3h, desc_3h, tags_3h, duracion_min=180, variante=3)
        resultados.append({'tipo': 'VIDEO 3H', 'titulo': titulo_3h, 'url': url})
        telegram(f"✅ <b>Video 3H subido</b>\n🎬 {titulo_3h}\n🔗 {url}")

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