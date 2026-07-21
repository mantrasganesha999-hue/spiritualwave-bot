import requests, subprocess, os, random, base64, pickle, io, json, time
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
    "mantra de Ganesha para emprendedores que buscan su primer cliente",
    "mantra de Ganesha para estudiantes antes de un examen importante",
    "mantra de Ganesha para madres solteras que buscan estabilidad",
    "mantra de Ganesha para quienes buscan trabajo urgente",
    "mantra de Ganesha para sanar deudas y salir de crisis financiera",
    "mantra de Ganesha para artistas y creativos que buscan inspiracion",
    "mantra de Ganesha para quienes empiezan un negocio nuevo",
    "mantra de Ganesha para parejas que buscan reconciliacion",
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
    "Ganesha mantra for entrepreneurs seeking their first client",
    "Ganesha mantra for students before an important exam",
    "Ganesha mantra for single mothers seeking stability",
    "Ganesha mantra for urgent job search success",
    "Ganesha mantra to heal debt and financial crisis",
    "Ganesha mantra for artists and creatives seeking inspiration",
    "Ganesha mantra for those starting a new business",
    "Ganesha mantra for couples seeking reconciliation",
]

TEMAS_PT = [
    "mantra de Ganesha para atrair abundancia e eliminar dividas",
    "frequencia 528hz para curar o corpo e atrair prosperidade",
    "afirmacoes poderosas para manifestar dinheiro todas as manhas",
    "meditacao guiada para eliminar energia negativa e atrair sucesso",
    "lei da atracao para atrair dinheiro abundancia e saude",
    "mantra poderoso de Ganesha para protecao e abundancia",
    "musica de cura 432hz para dormir e restaurar a alma",
    "mantra de Ganesha om gan ganapataye namaha poder e abundancia",
    "528hz frequencia milagre para curar e atrair prosperidade",
    "mantra de Ganesha para trabalho sucesso e prosperidade economica",
]

TEMAS_SHORTS_ES = [
    "Por que Ganesha elimina obstaculos al instante",
    "Que pasa si repites este mantra 21 veces",
    "Como atraer dinero en 60 segundos con Ganesha",
    "El error que comete el 90 porciento al pedir abundancia",
    "Por que 528hz cambia tu cerebro en un minuto",
    "Que significa realmente Om Gan Ganapataye Namaha",
    "Como saber si Ganesha ya escucho tu peticion",
    "El mantra que los ricos repiten cada manana",
    "Por que debes escuchar esto antes de dormir",
    "Como eliminar la mala suerte en 60 segundos",
    "Que frecuencia usar cuando todo sale mal",
    "El secreto de Ganesha que nadie te conto",
    "Como manifestar dinero mientras duermes",
    "Por que este mantra abre puertas cerradas",
    "Que hacer cuando sientes bloqueada tu abundancia",
    "Como activar tu suerte con este audio",
    "El ritual de 60 segundos para atraer prosperidad",
    "Por que Ganesha es el dios mas poderoso para el dinero",
    "Que pasa si escuchas 528hz siete dias seguidos",
    "Como limpiar tu energia en un minuto",
]

TEMAS_SHORTS_EN = [
    "Why Ganesha removes obstacles instantly",
    "What happens if you repeat this mantra 21 times",
    "How to attract money in 60 seconds with Ganesha",
    "The mistake 90 percent make when asking for abundance",
    "Why 528hz changes your brain in one minute",
    "What Om Gan Ganapataye Namaha really means",
    "How to know if Ganesha already heard your request",
    "The mantra rich people repeat every morning",
    "Why you should listen to this before sleeping",
    "How to remove bad luck in 60 seconds",
    "What frequency to use when everything goes wrong",
    "The Ganesha secret nobody told you",
    "How to manifest money while you sleep",
    "Why this mantra opens closed doors",
    "What to do when you feel blocked from abundance",
    "How to activate your luck with this audio",
    "The 60 second ritual to attract prosperity",
    "Why Ganesha is the most powerful god for money",
    "What happens if you listen to 528hz for 7 days",
    "How to clean your energy in one minute",
]

TEMAS_SHORTS_PT = [
    "Mantra de Ganesha para abundancia instantanea",
    "528hz frequencia milagre ativa agora",
    "Om Gan Ganapataye Namaha poder infinito",
    "Mantra de Ganesha elimina obstaculos hoje",
    "Ative sua abundancia com Ganesha agora",
]

TEMAS_HI = [
    "Ganesha mantra Om Gan Ganapataye Namaha for wealth and success",
    "Ganpati Bappa mantra to remove all obstacles and bring luck",
    "Powerful Ganesh mantra for money abundance and prosperity",
    "Vighnaharta Ganesha mantra to destroy all problems in life",
    "Ganpati mantra for business success and financial growth",
    "Shubh Ganesha mantra for good luck and positive energy",
    "Ganesh chaturthi special mantra for blessings and abundance",
    "Ganpati Bappa Morya mantra for happiness and prosperity",
]

TEMAS_SHORTS_HI = [
    "Why Ganpati Bappa removes all your problems instantly",
    "This Ganesh mantra brings money in 21 days",
    "Ganpati mantra for instant luck and success",
    "The most powerful Ganesha mantra for wealth",
    "Ganpati Bappa Morya mantra for happiness now",
]

DIAS_SERIE_21 = [
    "Dia 1: Reconoce que mereces la abundancia que pides",
    "Dia 2: Repite el mantra Om Gan Ganapataye con fe total",
    "Dia 3: Visualiza a Ganesha eliminando tus obstaculos",
    "Dia 4: Agradece por lo que ya tienes en tu vida",
    "Dia 5: Suelta el control y confia en el proceso divino",
    "Dia 6: Escribe tres deseos que quieres manifestar",
    "Dia 7: Medita en silencio 10 minutos con Ganesha",
    "Dia 8: Perdona a quien te ha hecho dano",
    "Dia 9: Actua como si ya tuvieras lo que deseas",
    "Dia 10: Comparte tu abundancia con alguien mas",
    "Dia 11: Elimina un pensamiento negativo hoy",
    "Dia 12: Conecta con la naturaleza y su energia",
    "Dia 13: Repite afirmaciones de merecimiento",
    "Dia 14: Celebra tus pequenos logros de este mes",
    "Dia 15: Pide ayuda a Ganesha para tu proposito",
    "Dia 16: Libera el miedo al fracaso definitivamente",
    "Dia 17: Confia en tu intuicion y sigue tu camino",
    "Dia 18: Bendice tu dinero y tus finanzas",
    "Dia 19: Rodeate de energia positiva y personas afines",
    "Dia 20: Prepara tu mente para recibir milagros",
    "Dia 21: Celebra tu transformacion y nueva abundancia",
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

def verificar_salud():
    print("Verificando salud del sistema...")
    problemas = []

    imagenes = get_imagenes()
    if len(imagenes) < 10:
        problemas.append(f"Solo {len(imagenes)} imagenes disponibles")

    musicas = get_musicas()
    if len(musicas) < 5:
        problemas.append(f"Solo {len(musicas)} musicas disponibles")

    if not GROQ_KEY:
        problemas.append("GROQ_API_KEY no configurada")

    if not YOUTUBE_TOKEN_B64:
        problemas.append("YOUTUBE_TOKEN no configurado")
    else:
        try:
            token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
            creds = pickle.loads(token_data)
            if creds.expired and not creds.refresh_token:
                problemas.append("Token de YouTube expirado sin refresh disponible")
        except Exception as e:
            problemas.append(f"Token de YouTube corrupto: {str(e)[:50]}")

    if problemas:
        msg = "⚠️ <b>Chequeo de salud - Problemas detectados</b>\n\n"
        for p in problemas:
            msg += f"❌ {p}\n"
        telegram(msg)
        print("PROBLEMAS DETECTADOS:", problemas)
    else:
        print("Sistema saludable, todo OK")

    return len(problemas) == 0

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

def obtener_dia_serie():
    archivo_estado = os.path.join(BASE, 'serie_dia.txt')
    try:
        with open(archivo_estado, 'r') as f:
            dia_actual = int(f.read().strip())
    except:
        dia_actual = 0

    dia_actual = (dia_actual % 21) + 1

    with open(archivo_estado, 'w') as f:
        f.write(str(dia_actual))

    return dia_actual

def generar_guion(tema, lang='es'):
    print(f"[1/4] Generando guion {lang}...")
    emoji = random.choice(EMOJIS_TITULO)
    if lang == 'es':
        prompt = f"""Eres experto en contenido espiritual de YouTube en espanol latino, actualizado en tendencias 2026.
Genera contenido VIRAL para un video sobre: {tema}
Sin tildes ni caracteres especiales ni asteriscos ni markdown.
Incluye en el titulo o descripcion terminos de tendencia actual como: manifestacion 2026, codigo 528, activacion cuantica, portal energetico, ano de la abundancia, cuando sea relevante al tema.
Responde EXACTAMENTE en este formato sin simbolos extra:
TITULO: {emoji} [titulo maximo 60 caracteres, impactante con numero, pregunta o referencia a 2026]
DESCRIPCION: [500 palabras con keywords espirituales de tendencia, beneficios, instrucciones de uso, CTA para suscribirse a youtube.com/@SpiritualWave888]
TAGS: [30 hashtags separados por espacios incluyendo terminos de tendencia 2026]"""
    else:
        prompt = f"""You are a viral spiritual YouTube expert, updated on 2026 trends.
Generate content for: {tema}
No asterisks, no markdown, no special symbols.
Include trending 2026 terms when relevant like: manifestation 2026, quantum activation, 528 code, energy portal, year of abundance.
Reply EXACTLY in this format:
TITULO: {emoji} [title maximum 60 characters, with number, question or 2026 reference]
DESCRIPCION: [500 words with trending spiritual keywords, benefits, how to use, CTA to subscribe to youtube.com/@SpiritualWave888]
TAGS: [30 relevant hashtags separated by spaces including 2026 trending terms]"""

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

def generar_thumbnail_short(titulo, variante=1):
    print(f"Generando thumbnail SHORT variante {variante}...")
    try:
        imagenes = get_imagenes()
        if not imagenes:
            return None

        img_path = imagenes[variante % len(imagenes)]
        img = Image.open(img_path)
        w, h = img.size
        target_ratio = 1080/1920
        if w/h > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
        img = img.resize((1080, 1920)).convert('RGB')

        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.35)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        for i in range(500):
            alpha = int(230 * (i / 500))
            d.rectangle([(0, img.height - 500 + i), (img.width, img.height - 499 + i)], fill=(0, 0, 0, alpha))
        d.rectangle([(0, 0), (img.width, 160)], fill=(0, 0, 0, 190))
        for thickness in range(6):
            color_val = max(150, 201 - thickness * 10)
            d.rectangle(
                [(thickness, thickness), (img.width-1-thickness, img.height-1-thickness)],
                outline=(color_val, int(color_val * 0.83), int(color_val * 0.37)),
                width=1
            )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        try:
            font_titulo = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 68)
            font_canal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 46)
        except:
            font_titulo = ImageFont.load_default()
            font_canal = ImageFont.load_default()

        canal = 'SpiritualWave'
        bbox = draw.textbbox((0, 0), canal, font=font_canal)
        w = bbox[2] - bbox[0]
        cx = (img.width - w) // 2
        draw.text((cx+4, 44), canal, fill=(100, 75, 0), font=font_canal)
        draw.text((cx, 40), canal, fill=(255, 220, 50), font=font_canal)

        titulo_clean = limpiar_texto(titulo.replace('#Shorts', ''))[:60]
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

        total_lines = min(len(lineas), 4)
        line_height = 80
        total_height = total_lines * line_height
        y_start = img.height - 470 + (470 - total_height) // 2

        for linea in lineas[:4]:
            bbox = draw.textbbox((0, 0), linea, font=font_titulo)
            w = bbox[2] - bbox[0]
            x = (img.width - w) // 2
            for dx, dy in [(-3,3),(3,3),(3,-3),(-3,-3),(0,4),(4,0),(0,-4),(-4,0)]:
                draw.text((x+dx, y_start+dy), linea, fill=(0, 0, 0), font=font_titulo)
            draw.text((x, y_start), linea, fill=(255, 255, 255), font=font_titulo)
            y_start += line_height

        path = f'/tmp/thumbnail_short_{variante}.jpg'
        img.save(path, 'JPEG', quality=98)
        print(f"  Thumbnail Short OK")
        return path
    except Exception as e:
        print(f"  Thumbnail Short error: {e}")
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

    if VIDEOS_SUBIDOS_HOY:
        caps += f"\nContinua tu practica espiritual con nuestro video anterior:\n"
        caps += f"https://www.youtube.com/watch?v={VIDEOS_SUBIDOS_HOY[-1]}\n"

    caps += f"\nSuscribete: youtube.com/@SpiritualWave888\n"
    caps += f"Activa la campana para no perderte nada\n"
    return descripcion + caps

def agregar_a_playlist(youtube, video_id, playlist_nombre):
    try:
        playlists = youtube.playlists().list(
            part='snippet', mine=True, maxResults=50
        ).execute()

        playlist_id = None
        for pl in playlists.get('items', []):
            if pl['snippet']['title'] == playlist_nombre:
                playlist_id = pl['id']
                break

        if not playlist_id:
            resp = youtube.playlists().insert(
                part='snippet,status',
                body={
                    'snippet': {
                        'title': playlist_nombre,
                        'description': f'Videos de {playlist_nombre} - SpiritualWave'
                    },
                    'status': {'privacyStatus': 'public'}
                }
            ).execute()
            playlist_id = resp['id']
            print(f"  Playlist creada: {playlist_nombre}")

        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {'kind': 'youtube#video', 'videoId': video_id}
                }
            }
        ).execute()
        print(f"  Agregado a playlist: {playlist_nombre}")
    except Exception as e:
        print(f"  Playlist error: {e}")

def subir_youtube(video_path, titulo, descripcion, tags, es_short=False, duracion_min=60, variante=1, playlist_nombre=None):
    print(f"Subiendo {'SHORT' if es_short else 'VIDEO'} a YouTube...")
    from google.auth.transport.requests import Request
    token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
    creds = pickle.loads(token_data)
    if creds.expired and creds.refresh_token:
        print("  Token expirado, renovando automaticamente...")
        creds.refresh(Request())
        print("  Token renovado OK")
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

    if es_short:
        thumb = generar_thumbnail_short(titulo, variante)
        if thumb:
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumb, mimetype='image/jpeg')
                ).execute()
                print("  Thumbnail Short OK")
            except Exception as e:
                print(f"  Thumbnail Short error: {e}")
    else:
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

        if VIDEOS_SUBIDOS_HOY:
            try:
                video_anterior = VIDEOS_SUBIDOS_HOY[-1]
                youtube.cards().insert(
                    videoId=video_id,
                    body={"card": {"videoIdCard": {"videoId": video_anterior}}}
                ).execute()
                print("  Card OK")
            except Exception as e:
                print(f"  Card error: {e}")

        VIDEOS_SUBIDOS_HOY.append(video_id)

        if playlist_nombre:
            agregar_a_playlist(youtube, video_id, playlist_nombre)

        try:
            comentarios_es = [
                "Que manifestaste hoy? Cuentame en los comentarios 🙏",
                "Cual fue tu experiencia con este mantra? Comparte abajo ✨",
                "Etiqueta a alguien que necesita escuchar esto hoy 🔱",
                "Deja tu Om en los comentarios si sentiste la energia 🕉",
                "Cuantos dias llevas practicando este mantra? 🙏",
                "Comparte este video con quien necesite abundancia hoy 💫",
                "Que frecuencia te gustaria en el proximo video? 🎵",
            ]
            comentarios_en = [
                "What did you manifest today? Tell me in the comments 🙏",
                "What was your experience with this mantra? Share below ✨",
                "Tag someone who needs to hear this today 🔱",
                "Leave your Om below if you felt the energy 🕉",
                "How many days have you been practicing this mantra? 🙏",
                "Share this video with someone who needs abundance today 💫",
                "What frequency would you like in the next video? 🎵",
            ]
            tiene_acentos = any(c in titulo for c in 'áéíóúñ')
            comentario = random.choice(comentarios_es if tiene_acentos else comentarios_en)
            comment_response = youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {"textOriginal": comentario}
                        }
                    }
                }
            ).execute()
            comment_id = comment_response['id']
            youtube.comments().setModerationStatus(
                id=comment_id,
                moderationStatus="published"
            ).execute()
            print("  Comentario publicado")
        except Exception as e:
            print(f"  Comentario error: {e}")

    return video_id, url

def montar_video_directo(titulo, duracion=6000):
    print(f"Montando video para directo {duracion//60}min...")
    imagenes = get_imagenes()
    musicas = get_musicas()
    if not imagenes or not musicas:
        return None

    musica = random.choice(musicas)
    lista_path = '/tmp/lista_directo.txt'
    salida = '/tmp/video_directo.mp4'
    dur_img = 20
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
        f"drawtext=text='{titulo[:40]}':fontcolor=white:fontsize=44:"
        "x=(w-text_w)/2:y=h-80:shadowcolor=black:shadowx=3:shadowy=3,"
        "drawtext=text='SpiritualWave LIVE':fontcolor=0xFFD700:fontsize=32:"
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
        print(f"  OK: {os.path.getsize(salida)//1024//1024}MB")
        return salida
    print(f"  Error: {result.stderr[-300:]}")
    return None

def crear_directo_youtube(titulo, descripcion, video_path):
    print("Creando transmision en vivo...")
    try:
        token_data = base64.b64decode(YOUTUBE_TOKEN_B64)
        creds = pickle.loads(token_data)
        youtube = build('youtube', 'v3', credentials=creds)

        broadcast = youtube.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body={
                "snippet": {
                    "title": titulo[:100],
                    "description": descripcion,
                    "scheduledStartTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True,
                    "recordFromStart": True
                }
            }
        ).execute()
        broadcast_id = broadcast['id']
        print(f"  Broadcast creado: {broadcast_id}")

        stream = youtube.liveStreams().insert(
            part="snippet,cdn",
            body={
                "snippet": {"title": f"Stream - {titulo[:80]}"},
                "cdn": {"frameRate": "30fps", "ingestionType": "rtmp", "resolution": "1080p"}
            }
        ).execute()
        stream_id = stream['id']
        stream_key = stream['cdn']['ingestionInfo']['streamName']
        rtmp_url = stream['cdn']['ingestionInfo']['ingestionAddress']

        youtube.liveBroadcasts().bind(
            part="id,contentDetails", id=broadcast_id, streamId=stream_id
        ).execute()

        print(f"  Transmitiendo hacia: {rtmp_url}/{stream_key}")

        cmd = [
            'ffmpeg', '-re', '-i', video_path,
            '-c:v', 'libx264', '-preset', 'veryfast', '-maxrate', '3000k', '-bufsize', '6000k',
            '-pix_fmt', 'yuv420p', '-g', '60', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
            '-f', 'flv', f'{rtmp_url}/{stream_key}'
        ]
        print("  Iniciando stream RTMP...")
        subprocess.run(cmd, timeout=6100)

        print("  Stream finalizado")
        return broadcast_id
    except Exception as e:
        print(f"  Error directo: {e}")
        return None

# MAIN
print("\n=== SPIRITUALWAVE AUTO PRODUCER HD ===")
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
resultados = []

verificar_salud()

telegram(f"🔱 <b>SpiritualWave Producer iniciado</b>\n📅 {fecha}\n⏳ Generando contenido + directo...")

try:
    tema_es = random.choice(TEMAS_ES)
    print(f"\n[VIDEO ES 1H] {tema_es}")
    titulo_es, desc_es, tags_es = generar_guion(tema_es, 'es')
    video_es = montar_video(titulo_es, duracion=3600)
    if video_es:
        vid_id, url = subir_youtube(video_es, titulo_es, desc_es, tags_es, duracion_min=60, variante=1, playlist_nombre="Mantras de Ganesha")
        resultados.append({'tipo': 'VIDEO ES 1H', 'titulo': titulo_es, 'url': url})
        telegram(f"✅ <b>Video ES 1H subido</b>\n🎬 {titulo_es}\n🔗 {url}")
except Exception as e:
    telegram(f"⚠️ Error en video ES: {str(e)[:150]}")
    print(f"Error video ES: {e}")

try:
    tema_short_es = random.choice(TEMAS_SHORTS_ES)
    print(f"\n[SHORT ES] {tema_short_es}")
    short_es = montar_video(tema_short_es, es_short=True)
    if short_es:
        vid_id, url = subir_youtube(short_es, tema_short_es, f"🙏 {tema_short_es}\n\nSuscribete: youtube.com/@SpiritualWave888\n\n#Ganesha #Shorts #Mantra #Espiritual #Abundancia #528hz", "#Ganesha #Shorts #Mantra #Espiritual #Abundancia #528hz #SpiritualWave", es_short=True, variante=2)
        resultados.append({'tipo': 'SHORT ES', 'titulo': tema_short_es, 'url': url})
        telegram(f"✅ <b>Short ES subido</b>\n🎬 {tema_short_es}\n🔗 {url}")
except Exception as e:
    telegram(f"⚠️ Error en Short ES: {str(e)[:150]}")
    print(f"Error Short ES: {e}")

try:
    tema_short_en = random.choice(TEMAS_SHORTS_EN)
    print(f"\n[SHORT EN] {tema_short_en}")
    short_en = montar_video(tema_short_en, es_short=True)
    if short_en:
        vid_id, url = subir_youtube(short_en, tema_short_en, f"🙏 {tema_short_en}\n\nSubscribe: youtube.com/@SpiritualWave888\n\n#Ganesha #Shorts #Mantra #Spiritual #Abundance #528hz", "#Ganesha #Shorts #Mantra #Spiritual #Abundance #528hz #SpiritualWave", es_short=True, variante=3)
        resultados.append({'tipo': 'SHORT EN', 'titulo': tema_short_en, 'url': url})
        telegram(f"✅ <b>Short EN subido</b>\n🎬 {tema_short_en}\n🔗 {url}")
except Exception as e:
    telegram(f"⚠️ Error en Short EN: {str(e)[:150]}")
    print(f"Error Short EN: {e}")

try:
    dia_serie = obtener_dia_serie()
    tema_serie = DIAS_SERIE_21[dia_serie - 1]
    titulo_serie = f"21 Dias con Ganesha - Dia {dia_serie}/21"
    print(f"\n[SERIE 21 DIAS] {titulo_serie}")

    prompt_serie = f"""Eres experto en contenido espiritual de YouTube.
Este es el Dia {dia_serie} de una serie de 21 dias de manifestacion con Ganesha.
El tema de hoy es: {tema_serie}
Sin tildes ni caracteres especiales ni asteriscos.
Genera una descripcion motivadora de 300 palabras sobre esta practica diaria, mencionando que es parte de la serie de 21 dias, invitando a suscribirse para no perderse los proximos dias.
Responde EXACTAMENTE:
DESCRIPCION: [descripcion de 300 palabras]
TAGS: [20 hashtags separados por espacios]"""

    r_serie = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt_serie}], 'max_tokens': 1200}
    )
    contenido_serie = r_serie.json()['choices'][0]['message']['content']
    desc_serie = extraer_campo(contenido_serie, 'DESCRIPCION', 'TAGS') or tema_serie
    desc_serie = limpiar_texto(desc_serie)
    tags_serie = extraer_campo(contenido_serie, 'TAGS') or "#Ganesha #21Dias #Manifestacion #SpiritualWave"
    tags_serie = limpiar_texto(tags_serie)

    video_serie = montar_video(titulo_serie, duracion=1800)
    if video_serie:
        vid_id, url = subir_youtube(video_serie, titulo_serie, desc_serie, tags_serie, duracion_min=30, variante=4, playlist_nombre="21 Dias con Ganesha")
        resultados.append({'tipo': 'SERIE 21D', 'titulo': titulo_serie, 'url': url})
        telegram(f"✅ <b>Serie 21 Dias subido</b>\n🎬 {titulo_serie}\n🔗 {url}")
except Exception as e:
    telegram(f"⚠️ Error en serie 21 dias: {str(e)[:150]}")
    print(f"Error serie: {e}")

try:
    tema_pt = random.choice(TEMAS_PT)
    print(f"\n[VIDEO PT] {tema_pt}")
    prompt_pt = f"""Voce e um especialista em conteudo espiritual do YouTube em portugues do Brasil.
Gere conteudo VIRAL para um video sobre: {tema_pt}
Sem acentos ou caracteres especiais nem asteriscos.
Responda EXATAMENTE neste formato:
TITULO: [titulo maximo 60 caracteres impactante]
DESCRICAO: [400 palavras com palavras chave espirituais, beneficios, CTA para se inscrever em youtube.com/@SpiritualWave888]
TAGS: [25 hashtags separadas por espacos]"""

    r_pt = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt_pt}], 'max_tokens': 1500}
    )
    contenido_pt = r_pt.json()['choices'][0]['message']['content']
    titulo_pt = extraer_campo(contenido_pt, 'TITULO', 'DESCRICAO') or tema_pt[:60]
    titulo_pt = limpiar_texto(titulo_pt)
    desc_pt = extraer_campo(contenido_pt, 'DESCRICAO', 'TAGS') or tema_pt
    desc_pt = limpiar_texto(desc_pt)
    tags_pt = extraer_campo(contenido_pt, 'TAGS') or "#Ganesha #Mantra #Espiritual #528hz"
    tags_pt = limpiar_texto(tags_pt)

    video_pt = montar_video(titulo_pt, duracion=3600)
    if video_pt:
        vid_id, url = subir_youtube(video_pt, titulo_pt, desc_pt, tags_pt, duracion_min=60, variante=5, playlist_nombre="Mantras em Portugues")
        resultados.append({'tipo': 'VIDEO PT', 'titulo': titulo_pt, 'url': url})
        telegram(f"✅ <b>Video PT subido</b>\n🎬 {titulo_pt}\n🔗 {url}")
except Exception as e:
    telegram(f"⚠️ Error en video PT: {str(e)[:150]}")
    print(f"Error PT: {e}")

try:
    tema_hi = random.choice(TEMAS_HI)
    print(f"\n[VIDEO HI] {tema_hi}")
    prompt_hi = f"""You are an expert in Hindu spiritual YouTube content for Indian audience.
Generate VIRAL content for a video about: {tema_hi}
Use English but include devotional Hindi terms like Ganpati Bappa, Vighnaharta, Shubh, Mangal when natural.
No asterisks, no markdown.
Reply EXACTLY in this format:
TITULO: [title maximum 60 characters, impactful, include Ganpati or Ganesha]
DESCRIPCION: [400 words with devotional keywords, benefits, CTA to subscribe to youtube.com/@SpiritualWave888]
TAGS: [30 hashtags separated by spaces including Ganpati GaneshChaturthi VighnahartaGanesh]"""

    r_hi = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt_hi}], 'max_tokens': 1500}
    )
    contenido_hi = r_hi.json()['choices'][0]['message']['content']
    titulo_hi = extraer_campo(contenido_hi, 'TITULO', 'DESCRIPCION') or tema_hi[:60]
    titulo_hi = limpiar_texto(titulo_hi)
    desc_hi = extraer_campo(contenido_hi, 'DESCRIPCION', 'TAGS') or tema_hi
    desc_hi = limpiar_texto(desc_hi)
    tags_hi = extraer_campo(contenido_hi, 'TAGS') or "#Ganpati #Ganesha #Mantra #Vighnaharta #SpiritualWave"
    tags_hi = limpiar_texto(tags_hi)

    video_hi = montar_video(titulo_hi, duracion=3600)
    if video_hi:
        vid_id, url = subir_youtube(video_hi, titulo_hi, desc_hi, tags_hi, duracion_min=60, variante=6, playlist_nombre="Ganpati Bappa Mantras")
        resultados.append({'tipo': 'VIDEO HI', 'titulo': titulo_hi, 'url': url})
        telegram(f"✅ <b>Video HI (India) subido</b>\n🎬 {titulo_hi}\n🔗 {url}")
except Exception as e:
    telegram(f"⚠️ Error en video HI: {str(e)[:150]}")
    print(f"Error HI: {e}")

resumen = f"🔱 <b>Videos completados</b>\n📅 {fecha}\n\n"
for r in resultados:
    resumen += f"✅ {r['tipo']}: {r['titulo'][:40]}\n"
telegram(resumen)

try:
    titulo_live = "🔱 Ganesha 528Hz Live - Musica Espiritual - SpiritualWave"
    desc_live = "Transmision en vivo de musica espiritual con mantras de Ganesha y frecuencias 528hz.\n\nSuscribete: youtube.com/@SpiritualWave888\n\n#Ganesha #Live #528hz #Meditacion"

    telegram(f"🔴 <b>Iniciando transmision en vivo</b>\n📅 {fecha}\n⏳ Duracion: ~1.5 horas")
    video_live = montar_video_directo(titulo_live, duracion=6000)
    if video_live:
        broadcast_id = crear_directo_youtube(titulo_live, desc_live, video_live)
        if broadcast_id:
            telegram(f"🔴 <b>Directo finalizado</b>\n🔗 https://www.youtube.com/watch?v={broadcast_id}")
        else:
            telegram("⚠️ El directo fallo pero los videos ya se subieron correctamente")
    else:
        telegram("⚠️ No se pudo generar el video para el directo")
except Exception as e:
    telegram(f"⚠️ <b>Error en el directo (no afecta videos ya subidos)</b>\n{str(e)[:200]}")
    print(f"Error directo: {e}")

print("\n=== PROCESO FINALIZADO ===")