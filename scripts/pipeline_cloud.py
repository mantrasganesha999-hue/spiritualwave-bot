import requests, subprocess, os, random, base64, pickle, io, json, time, re, sys, shutil, textwrap
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

GROQ_KEY = os.environ.get('GROQ_API_KEY')
YOUTUBE_TOKEN_B64 = os.environ.get('YOUTUBE_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notificar

TEMAS_ES = [
    "mantra de Ganesha para atraer abundancia y eliminar obstaculos",
    "musica espiritual de Ganesha para meditar profundamente",
    "om gan ganapataye namaha el mantra mas poderoso de Ganesha",
    "ganesha mantra para el trabajo el exito y la prosperidad",
    "musica de Ganesha para dormir en paz y despertar renovado",
    "mantra poderoso de Ganesha para proteccion y bendiciones",
    "musica tibetana con Ganesha para calmar la mente",
    "ganesha mantra para superar obstaculos y lograr tus metas",
    "musica de Ganesha para reducir el estres y encontrar calma",
    "mantra de la prosperidad con Ganesha para 21 dias",
    "mantra sagrado de Ganesha para atraer bendiciones diarias",
    "musica con mantras de Ganesha para atraer amor y paz",
    "mantra de Lakshmi y Ganesha para riqueza y prosperidad",
    "musica devocional de Ganesha para el alma y el corazon",
    "ganesha mantra para proteger el hogar y la familia",
    "mantra de Ganesha para emprendedores en busca de exito",
    "mantra de Ganesha para estudiantes antes de un examen",
    "mantra de Ganesha para quienes buscan trabajo urgente",
    "mantra de Ganesha para sanar deudas y crisis financiera",
    "mantra de Ganesha para artistas que buscan inspiracion",
    "mantra de Ganesha para parejas que buscan reconciliacion",
    "bhajan de Ganesha para celebrar y agradecer",
    "musica de cuencos tibetanos con mantra de Ganesha",
    "ganesha mantra para la mañana llena de energia positiva",
    "mantra de Ganesha para dormir sin preocupaciones",
]

TEMAS_EN = [
    "Powerful Ganesha chant to attract abundance and remove obstacles",
    "Om Gan Ganapataye Namaha the most powerful Ganesha mantra",
    "Ganesha mantra for success career and financial prosperity",
    "Ganesha morning mantra for positive energy and good luck",
    "Tibetan singing bowls with Ganesha mantra for deep focus",
    "Ganesha sleep music to remove obstacles while you rest",
    "Ganesha mantra for students success and mental clarity",
    "Ganesha 1000 names chant for blessing and protection",
    "Ganesha mantra for new beginnings and a fresh start",
    "Ganesha divine music for yoga and deep meditation",
    "Ganesha mantra for entrepreneurs seeking their first client",
    "Ganesha mantra for urgent job search success",
    "Ganesha mantra to overcome debt and financial difficulty",
    "Ganesha mantra for artists and creatives seeking inspiration",
    "Ganesha mantra for couples seeking reconciliation",
    "Deep meditation music with Ganesha chant for inner peace",
    "Sacred Ganesha bhajan for daily devotion and gratitude",
    "Ganesha mantra for protection of home and family",
    "Om Namah Shivaya with Ganesha mantra devotional music",
    "Ganesha blessing chant for health wealth and happiness",
    "Ganesha meditation for beginners simple and powerful",
    "Ganesha mantra to start the day with positive intention",
    "Devotional Ganesha music for evening prayer and peace",
    "Ganesha chant to calm the mind before sleeping",
    "Powerful Ganpati mantra for removing all life obstacles",
]

TEMAS_PT = [
    "mantra de Ganesha para atrair abundancia e eliminar obstaculos",
    "musica espiritual de Ganesha para meditar profundamente",
    "mantra de Ganesha om gan ganapataye namaha poder e prosperidade",
    "musica de Ganesha para dormir em paz e despertar renovado",
    "mantra de Ganesha para trabalho sucesso e prosperidade",
    "meditacao com mantras de Ganesha para paz interior",
    "musica relaxante de Ganesha para reduzir o estresse",
    "mantra de Ganesha para superar obstaculos e atingir metas",
    "bhajan devocional de Ganesha para gratidao diaria",
    "mantra de Ganesha para proteger o lar e a familia",
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
TEMAS_SHORTS_DEVOCIONAL = [
    "Jai Maa Kali mantra para proteccion y poder divino",
    "Mantra de Durga para eliminar todo mal",
    "Om Namah Shivaya para paz y transformacion interior",
    "Mantra de Lakshmi para riqueza instantanea",
    "Aarti poderosa para bendiciones diarias",
    "Stotram sagrado para eliminar obstaculos",
    "Bhajan devocional para sanar el alma",
    "Mantra de Hanuman para valor y proteccion",
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

EMOJIS_COMBOS = ["\u2728\U0001F531\U0001F338", "\U0001F525\u2728\U0001F549", "\U0001F64F\U0001F4AB\U0001F531",
                 "\u26A1\U0001F31F\U0001F549", "\U0001F525\U0001F64F\u2728", "\U0001F4AB\U0001F549\U0001F338"]

FRASES_ES = [
    "Abro mi mente a la abundancia infinita",
    "Ganesha elimina todos mis obstaculos",
    "Merezco la prosperidad que estoy manifestando",
    "Mi energia atrae dinero y bendiciones",
    "Confio en el proceso divino de mi vida",
    "Cada dia atraigo mas abundancia y paz",
    "Soy un iman para el exito y la riqueza",
    "Libero el miedo y abrazo la prosperidad",
    "El universo conspira a mi favor siempre",
    "Mi mente esta alineada con la abundancia",
    "Agradezco todo lo que ya tengo en mi vida",
    "Estoy listo para recibir milagros hoy",
]

FRASES_EN = [
    "I open my mind to infinite abundance",
    "Ganesha removes all my obstacles now",
    "I deserve the prosperity I am manifesting",
    "My energy attracts money and blessings",
    "I trust the divine process of my life",
    "Every day I attract more abundance and peace",
    "I am a magnet for success and wealth",
    "I release fear and embrace prosperity",
    "The universe always conspires in my favor",
    "My mind is aligned with abundance",
    "I am grateful for everything I already have",
    "I am ready to receive miracles today",
]

VIDEOS_SUBIDOS_HOY = []
DETALLE_SUBIDA = {}  # lo que salio bien/mal en la ultima subida (para el aviso de Telegram)

def telegram(mensaje):
    """Compatibilidad: envia texto HTML ya formateado."""
    return notificar.enviar(mensaje)

def get_imagenes():
    folder = os.path.join(BASE, 'assets/backgrounds')
    imgs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.startswith('ganesha') and f.endswith('.jpg')
    ]
    random.shuffle(imgs)
    return imgs

def get_imagenes_shorts():
    folder = os.path.join(BASE, 'assets/backgrounds_shorts')
    if not os.path.exists(folder):
        return get_imagenes()
    imgs = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.startswith('ganesha_short') and f.endswith('.jpg')
    ]
    if not imgs:
        return get_imagenes()
    random.shuffle(imgs)
    return imgs

def get_clips_ganesha(es_short=False):
    if es_short:
        folder = os.path.join(BASE, 'assets/videos_ganesha')
        prefijo = 'ganesha_clip'
    else:
        folder = os.path.join(BASE, 'assets/videos_ganesha_horizontal')
        prefijo = 'ganesha_h'
    if not os.path.exists(folder):
        return []
    clips = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.startswith(prefijo) and f.endswith('.mp4')
    ]
    random.shuffle(clips)
    return clips

def get_musicas(categoria='general'):
    folder = os.path.join(BASE, 'assets/music')
    todos = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    mantras = [f for f in todos if any(w in f.lower() for w in ['om', 'mantra', 'chant', 'gayatri', 'shiva', 'hanuman', 'hindu', 'bhajan', 'ram', 'krishna'])]
    meditation = [f for f in todos if any(w in f.lower() for w in ['meditation', 'meditat', 'zen', 'deep', 'buddhist', 'binaural'])]
    ambient = [f for f in todos if any(w in f.lower() for w in ['ambient', 'calm', 'relaxing', 'dreamscape', 'flute', 'bell'])]
    uplifting = [f for f in todos if any(w in f.lower() for w in ['uplifting', 'inspirational', 'corporate'])]
    if categoria == 'mantra' and mantras:
        seleccion = mantras
    elif categoria == 'meditation' and meditation:
        seleccion = meditation
    elif categoria == 'ambient' and ambient:
        seleccion = ambient
    elif categoria == 'uplifting' and uplifting:
        seleccion = uplifting
    else:
        seleccion = todos
    return [os.path.join(folder, f) for f in seleccion]

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
        notificar.salud(problemas)
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

def detectar_festival_hindu():
    hoy = datetime.now()
    mes = hoy.month
    dia = hoy.day
    festivales = {
        (8, 15): "Ganesh Chaturthi", (8, 16): "Ganesh Chaturthi", (8, 17): "Ganesh Chaturthi",
        (8, 18): "Ganesh Chaturthi", (8, 19): "Ganesh Chaturthi", (8, 20): "Ganesh Chaturthi",
        (8, 21): "Ganesh Chaturthi", (8, 22): "Ganesh Chaturthi", (8, 23): "Ganesh Chaturthi",
        (8, 24): "Ganesh Chaturthi", (8, 25): "Ganesh Chaturthi",
        (10, 1): "Navratri", (10, 2): "Navratri", (10, 3): "Navratri", (10, 4): "Navratri",
        (10, 5): "Navratri", (10, 6): "Navratri", (10, 7): "Navratri", (10, 8): "Navratri",
        (10, 9): "Navratri", (10, 10): "Navratri",
        (10, 20): "Diwali", (10, 21): "Diwali", (10, 22): "Diwali", (10, 23): "Diwali",
        (10, 24): "Diwali", (10, 25): "Diwali", (10, 26): "Diwali", (10, 27): "Diwali",
        (10, 28): "Diwali", (10, 29): "Diwali", (10, 30): "Diwali", (10, 31): "Diwali",
        (11, 1): "Diwali", (11, 2): "Diwali",
    }
    return festivales.get((mes, dia), None)

def generar_guion(tema, lang='es'):
    print(f"[1/4] Generando guion {lang}...")
    emoji = random.choice(EMOJIS_COMBOS)
    if lang == 'es':
        prompt = f"""Eres experto en contenido espiritual para YouTube. Crea contenido honesto y devocional sobre: {tema}
Sin tildes ni caracteres especiales ni asteriscos ni markdown.
No hagas promesas de salud, curacion o resultados garantizados.
El titulo debe describir exactamente lo que contiene el video.

Responde EXACTAMENTE en este formato sin simbolos extra:
TITULO: {emoji} [titulo descriptivo, maximo 90 caracteres, con mayusculas en palabras clave, que genere curiosidad y engagement]
DESCRIPCION: [300 palabras describiendo el contenido del video, beneficios espirituales de la practica del mantra, CTA para suscribirse a youtube.com/@SpiritualWave888. Incluir al final: "La musica, las imagenes y los videos fueron creados con herramientas de inteligencia artificial."]
TAGS: [5 hashtags separados por espacios, los mas relevantes para el video]"""
    else:
        prompt = f"""You are an expert in spiritual content for YouTube. Create honest and devotional content about: {tema}
No asterisks, no markdown, no special symbols.
Do not make health claims, healing promises, or guaranteed results.
The title must describe exactly what the video contains.

Reply EXACTLY in this format:
TITULO: {emoji} [descriptive title, maximum 60 characters, capitalize key words]
DESCRIPCION: [300 words describing the video content, spiritual benefits of mantra practice, CTA to subscribe to youtube.com/@SpiritualWave888. Include at the end: "The music, images and videos were created with artificial intelligence tools."]
TAGS: [5 relevant hashtags separated by spaces, the most relevant for the video]"""

    try:
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openai/gpt-oss-120b', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2000},
            timeout=30
        )
        data = r.json()
        if 'choices' not in data:
            print(f'  Groq error: {data}')
            return f'{emoji} {tema[:55]}', desc_fallback(tema, lang), '#Ganesha #Mantra #Espiritual #Bhakti #SpiritualWave'
        contenido = data['choices'][0]['message']['content']
    except Exception as e:
        print(f'  Groq exception: {e}')
        return f'{emoji} {tema[:55]}', desc_fallback(tema, lang), '#Ganesha #Mantra #Espiritual #Bhakti #SpiritualWave' 

    titulo = extraer_campo(contenido, 'TITULO', 'DESCRIPCION') or f"{emoji} {tema[:90]}"
    titulo = limpiar_texto(titulo)
    if len(titulo) > 95:
        titulo = titulo[:95].strip()

    descripcion = extraer_campo(contenido, 'DESCRIPCION', 'TAGS') or f"Video sobre {tema}"
    descripcion = limpiar_texto(descripcion)

    tags = extraer_campo(contenido, 'TAGS') or "#Ganesha #Mantra #Espiritual #528hz #Abundancia #Bhakti #Devocional #JaiGanesh #Mantra2026 #SanatanDharma #MusicaEspiritual #Meditacion"
    tags = limpiar_texto(tags)

    return titulo, descripcion, tags

def generar_thumbnail(titulo, variante=1, texto_marca='SpiritualWave', subtexto='Mantras & Frecuencias Divinas'):
    print(f"Generando thumbnail profesional variante {variante}...")
    try:
        imagenes = get_imagenes()
        if not imagenes:
            return None

        img_path = imagenes[variante % len(imagenes)]
        img = Image.open(img_path).resize((1920, 1080)).convert('RGB')

        # Saturacion y contraste mas vibrantes
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.6)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)

        paletas_borde = [
            (255, 200, 0),    # Oro brillante
            (255, 140, 0),    # Naranja dorado
            (220, 60, 0),     # Naranja fuego
            (180, 0, 180),    # Purpura sagrado
            (0, 180, 120),    # Verde esmeralda
        ]
        color_base = paletas_borde[variante % len(paletas_borde)]

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)

        # Gradiente inferior dramatico - mas alto (400px)
        for i in range(400):
            alpha = int(240 * (i / 400) ** 0.7)
            d.rectangle(
                [(0, img.height - 400 + i), (img.width, img.height - 399 + i)],
                fill=(0, 0, 0, alpha)
            )

        # Barra superior con tono dorado oscuro
        for i in range(140):
            alpha = int(200 * (1 - i/140) ** 0.5)
            d.rectangle([(0, i), (img.width, i+1)], fill=(20, 10, 0, alpha))

        # Borde dorado dramatico - 16px
        for thickness in range(16):
            factor = max(0.4, 1 - thickness * 0.04)
            color_borde = (int(color_base[0]*factor), int(color_base[1]*factor), int(color_base[2]*factor))
            d.rectangle(
                [(thickness, thickness), (img.width-1-thickness, img.height-1-thickness)],
                outline=color_borde,
                width=1
            )

        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        try:
            font_titulo = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 96)
            font_canal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 52)
            font_sub = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 34)
        except:
            font_titulo = ImageFont.load_default()
            font_canal = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        canal = texto_marca
        bbox = draw.textbbox((0, 0), canal, font=font_canal)
        w = bbox[2] - bbox[0]
        cx = (img.width - w) // 2
        # Glow efecto para nombre del canal
        for glow_r in range(8, 0, -2):
            glow_alpha = int(80 * (1 - glow_r/10))
            for gdx in range(-glow_r, glow_r+1, 2):
                for gdy in range(-glow_r, glow_r+1, 2):
                    draw.text((cx+gdx, 32+gdy), canal, fill=(255, 180, 0, glow_alpha), font=font_canal)
        draw.text((cx+5, 37), canal, fill=(100, 60, 0), font=font_canal)
        draw.text((cx+3, 35), canal, fill=(180, 120, 0), font=font_canal)
        draw.text((cx, 32), canal, fill=(255, 230, 60), font=font_canal)

        sub = subtexto
        bbox = draw.textbbox((0, 0), sub, font=font_sub)
        w = bbox[2] - bbox[0]
        draw.text(((img.width-w)//2+2, 97), sub, fill=(100, 70, 0), font=font_sub)
        draw.text(((img.width-w)//2, 95), sub, fill=(240, 200, 80), font=font_sub)

        titulo_clean = texto_visual(titulo, 65)
        palabras = titulo_clean.split()
        lineas = []
        linea = ""
        for p in palabras:
            test = linea + " " + p if linea else p
            bbox_test = draw.textbbox((0, 0), test, font=font_titulo)
            if bbox_test[2] - bbox_test[0] < img.width - 80:
                linea = test
            else:
                if linea:
                    lineas.append(linea)
                linea = p
        if linea:
            lineas.append(linea)

        total_lines = min(len(lineas), 3)
        line_height = 110
        total_height = total_lines * line_height
        y_start = img.height - 380 + (380 - total_height) // 2

        for linea in lineas[:3]:
            bbox = draw.textbbox((0, 0), linea, font=font_titulo)
            w = bbox[2] - bbox[0]
            x = (img.width - w) // 2

            # Glow dorado suave detras del texto blanco
            for glow_r in [6, 4, 2]:
                glow_color = (255, 180, 0, int(60 * (1 - glow_r/8)))
                for gdx in range(-glow_r, glow_r+1, 2):
                    for gdy in range(-glow_r, glow_r+1, 2):
                        draw.text((x+gdx, y_start+gdy), linea, fill=glow_color, font=font_titulo)

            # Sombra negra fuerte
            for dx, dy in [(-5,5),(5,5),(5,-5),(-5,-5),(0,6),(6,0),(0,-6),(-6,0),(-4,4),(4,4),(4,-4),(-4,-4)]:
                draw.text((x+dx, y_start+dy), linea, fill=(0, 0, 0), font=font_titulo)

            # Texto blanco brillante
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

        # Saturacion y contraste muy vibrantes para SHORT
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.65)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        # Gradiente inferior largo y dramatico
        for i in range(600):
            alpha = int(245 * (i / 600) ** 0.7)
            d.rectangle([(0, img.height - 600 + i), (img.width, img.height - 599 + i)], fill=(0, 0, 0, alpha))
        # Barra superior con tono calido
        for i in range(180):
            alpha = int(210 * (1 - i/180) ** 0.5)
            d.rectangle([(0, i), (img.width, i+1)], fill=(20, 10, 0, alpha))
        # Borde dorado dramatico
        for thickness in range(14):
            factor = max(0.4, 1 - thickness * 0.04)
            color_val = int(255 * factor)
            d.rectangle(
                [(thickness, thickness), (img.width-1-thickness, img.height-1-thickness)],
                outline=(color_val, int(color_val * 0.78), 0),
                width=1
            )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        try:
            font_titulo = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 76)
            font_canal = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 54)
        except:
            font_titulo = ImageFont.load_default()
            font_canal = ImageFont.load_default()

        canal = 'SpiritualWave'
        bbox = draw.textbbox((0, 0), canal, font=font_canal)
        w = bbox[2] - bbox[0]
        cx = (img.width - w) // 2
        # Glow dorado para canal
        for glow_r in [8, 5, 3]:
            for gdx in range(-glow_r, glow_r+1, 3):
                for gdy in range(-glow_r, glow_r+1, 3):
                    draw.text((cx+gdx, 45+gdy), canal, fill=(255, 160, 0, int(50*(1-glow_r/10))), font=font_canal)
        draw.text((cx+5, 50), canal, fill=(100, 60, 0), font=font_canal)
        draw.text((cx+3, 48), canal, fill=(180, 120, 0), font=font_canal)
        draw.text((cx, 45), canal, fill=(255, 230, 60), font=font_canal)

        titulo_clean = texto_visual(titulo, 65)
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
        line_height = 88
        total_height = total_lines * line_height
        y_start = img.height - 560 + (560 - total_height) // 2

        for linea in lineas[:4]:
            bbox = draw.textbbox((0, 0), linea, font=font_titulo)
            w = bbox[2] - bbox[0]
            x = (img.width - w) // 2
            # Glow dorado suave
            for glow_r in [5, 3]:
                for gdx in range(-glow_r, glow_r+1, 2):
                    for gdy in range(-glow_r, glow_r+1, 2):
                        draw.text((x+gdx, y_start+gdy), linea, fill=(255, 180, 0, int(55*(1-glow_r/7))), font=font_titulo)
            for dx, dy in [(-4,4),(4,4),(4,-4),(-4,-4),(0,5),(5,0),(0,-5),(-5,0)]:
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

def crear_mezcla_audio(duracion, salida='/tmp/mezcla_audio.m4a'):
    """Playlist de varias canciones (sin repetir seguidas) con volumen
    normalizado y fade in/out, en vez de una sola cancion en loop."""
    musicas = get_musicas()
    if not musicas:
        return None
    try:
        largos = {}
        for m in musicas:
            r = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=nw=1:nk=1', m],
                capture_output=True, text=True)
            try:
                largos[m] = float(r.stdout.strip())
            except ValueError:
                pass
        musicas = [m for m in musicas if m in largos and largos[m] > 20]
        if not musicas:
            return None

        orden, total, ultimo = [], 0.0, None
        while total < duracion + 10:
            ciclo = musicas.copy()
            random.shuffle(ciclo)
            if len(ciclo) > 1 and ciclo[0] == ultimo:
                ciclo[0], ciclo[-1] = ciclo[-1], ciclo[0]
            for m in ciclo:
                orden.append(m)
                total += largos[m]
                ultimo = m
                if total >= duracion + 10:
                    break

        lista = '/tmp/lista_audio.txt'
        with open(lista, 'w') as f:
            for m in orden:
                f.write("file '" + m.replace("'", "'\\''") + "'\n")

        fade_out_ini = max(0, duracion - 6)
        af = (f"loudnorm=I=-16:TP=-1.5:LRA=11,"
              f"afade=t=in:st=0:d=3,afade=t=out:st={fade_out_ini}:d=6")
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
               '-t', str(duracion), '-af', af, '-ar', '44100', '-ac', '2',
               '-c:a', 'aac', '-b:a', '192k', salida]
        subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(salida) and os.path.getsize(salida) > 100000:
            print(f"  Mezcla de audio OK: {len(orden)} pistas, {len(set(orden))} distintas")
            return salida
    except Exception as e:
        print(f"  Mezcla audio error: {e}")
    return None

FUENTE_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
TRANSICIONES = ['fade', 'dissolve']  # cruces suaves; el negro solo en los extremos de cada segmento
# Tratamiento de color (saturacion/contraste) aplicado a cada segmento
GRADE_VIDEO = ",eq=saturation=1.18:contrast=1.05:brightness=0.01"
DURACION_LARGO = int(os.environ.get('DURACION_LARGO', 900))  # 15 min por defecto


def texto_visual(texto, maxlen=60):
    """Texto seguro para dibujar (FFmpeg drawtext / PIL): sin emojis ni signos raros."""
    t = limpiar_texto((texto or '').replace('#Shorts', ''))
    t = re.sub(r"[^\w\s\-\.\!\?&,]", '', t)
    t = ' '.join(t.split())
    if len(t) > maxlen:
        t = t[:maxlen].rsplit(' ', 1)[0]
    return t.strip()


def lista_tags(tags):
    """Tags reales de YouTube (sin #), mezcla de los generados y los base del canal."""
    base = ['Ganesha mantra', 'Om Gan Ganapataye Namaha', 'Ganpati Bappa',
            'meditation music', 'spiritual music', '528hz']
    propios = [t.strip('#').strip() for t in (tags or '').split() if t.strip('#').strip()]
    salida, total, vistos = [], 0, set()
    for t in propios + base:
        if t.lower() in vistos:
            continue
        if total + len(t) + 1 > 450:
            break
        vistos.add(t.lower())
        salida.append(t)
        total += len(t) + 1
    return salida


def desc_fallback(tema, lang):
    if lang == 'es':
        return f'Video sobre {tema}\n\nLa musica, las imagenes y los videos fueron creados con herramientas de inteligencia artificial.'
    return f'Video about {tema}\n\nThe music, images and videos were created with artificial intelligence tools.'


def duracion_media(path):
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=nw=1:nk=1', path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def normalizar_clip(clip, salida, w, h, fps, max_seg=8):
    """Escala/recorta un clip al formato final. Devuelve su duracion (0 si falla)."""
    vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"setsar=1,fps={fps},format=yuv420p")
    subprocess.run(
        ['ffmpeg', '-y', '-i', clip, '-vf', vf, '-an', '-t', str(max_seg),
         '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18', salida],
        capture_output=True, text=True)
    if os.path.exists(salida):
        d = duracion_media(salida)
        if d >= 3:
            return d
    return 0.0


def render_segmento(clips, durs, salida, w, h, fps, vf_post='', xd=1.2,
                    enc=None):
    """Une clips con transiciones xfade + fade in/out en los extremos.
    Devuelve la duracion total del segmento o None si falla."""
    n = len(clips)
    if n == 0:
        return None
    cmd = ['ffmpeg', '-y']
    for c in clips:
        cmd += ['-i', c]
    partes = []
    prev = '[0:v]'
    acum = durs[0]
    for k in range(1, n):
        off = acum - xd
        trans = random.choice(TRANSICIONES)
        out = f'[v{k}]'
        partes.append(f"{prev}[{k}:v]xfade=transition={trans}:duration={xd}:offset={off:.3f}{out}")
        prev = out
        acum = acum + durs[k] - xd
    total = acum
    partes.append(
        f"{prev}fade=t=in:st=0:d=0.8,fade=t=out:st={max(0, total - 0.8):.3f}:d=0.8"
        f"{vf_post},format=yuv420p[vout]")
    if enc is None:
        enc = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-r', str(fps)]
    cmd += ['-filter_complex', ';'.join(partes), '-map', '[vout]', '-an', *enc, salida]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(salida) and os.path.getsize(salida) > 10000:
        return total
    print(f"  Segmento error: {r.stderr[-400:]}")
    return None


def construir_segmentos(es_short, w, h, fps, trabajo, n_clips, por_segmento,
                        vf_post='', enc=None):
    """Normaliza clips reales (o imagenes con zoom como respaldo) y arma segmentos."""
    normalizados = []  # (path, duracion)
    clips = get_clips_ganesha(es_short=es_short)
    if len(clips) >= 3:
        print(f"  Usando clips de video reales ({len(clips)} disponibles, {n_clips} en este video)")
        for idx, clip in enumerate(clips[:n_clips]):
            p = f'{trabajo}/n{idx}.mp4'
            d = normalizar_clip(clip, p, w, h, fps)
            if d:
                normalizados.append((p, d))
    if len(normalizados) < 3:
        print("  Usando imagenes con zoom (respaldo)")
        normalizados = []
        imagenes = get_imagenes_shorts() if es_short else get_imagenes()
        dur_img = 6
        for idx, img in enumerate(imagenes[:max(8, por_segmento)]):
            p = f'{trabajo}/z{idx}.mp4'
            zoom_expr = ("min(zoom+0.0012,1.25)" if idx % 2 == 0
                         else "if(eq(on,1),1.25,max(1.0,zoom-0.0012))")
            vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
                  f"zoompan=z='{zoom_expr}':d={dur_img*fps}:s={w}x{h}:fps={fps},format=yuv420p")
            subprocess.run(
                ['ffmpeg', '-y', '-loop', '1', '-i', img, '-vf', vf, '-t', str(dur_img),
                 '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '20', p],
                capture_output=True, text=True)
            if os.path.exists(p):
                d = duracion_media(p)
                if d >= 3:
                    normalizados.append((p, d))
    segmentos = []
    for i in range(0, len(normalizados), por_segmento):
        grupo = normalizados[i:i + por_segmento]
        if len(grupo) < 3 and segmentos:
            break
        seg = f'{trabajo}/seg{len(segmentos)}.mp4'
        total = render_segmento([g[0] for g in grupo], [g[1] for g in grupo],
                                seg, w, h, fps, vf_post=vf_post, enc=enc)
        if total:
            segmentos.append((seg, total))
    return segmentos


def filtros_texto(titulo_txt, es_short, t_total):
    """Titulo (en varias lineas) que aparece/desaparece, marca fija y CTA final."""
    font = f"fontfile={FUENTE_BOLD}:" if os.path.exists(FUENTE_BOLD) else ""
    borde = "borderw=3:bordercolor=black:shadowcolor=black:shadowx=3:shadowy=3"
    if es_short:
        ciclo, visible, tam, base, ancho = 100000, 6, 52, 300, 1080
        marca_tam, marca_x, marca_y = 36, '(w-text_w)/2', 110
    else:
        ciclo, visible, tam, base, ancho = 300, 12, 64, 120, 1920
        marca_tam, marca_x, marca_y = 32, 'w-text_w-40', 30
    m = f"mod(t,{ciclo})"
    por_linea = max(12, int(ancho * 0.88 / (tam * 0.70)))
    lineas = textwrap.wrap(titulo_txt, width=por_linea, break_long_words=False)[:3] or [titulo_txt]
    alto = int(tam * 1.25)
    filtros = []
    for i, linea in enumerate(lineas):
        y = f"h-{base + (len(lineas) - 1 - i) * alto}"
        filtros.append(
            f"drawtext={font}text='{linea}':fontcolor=0xFFD700:fontsize={tam}:"
            f"x=(w-text_w)/2:y={y}:{borde}:"
            f"enable='lt({m},{visible})':alpha='min(1,min({m},{visible}-{m}))'")
    filtros.append(
        f"drawtext={font}text='SpiritualWave':fontcolor=0xFFD700@0.85:fontsize={marca_tam}:"
        f"x={marca_x}:y={marca_y}:borderw=2:bordercolor=black@0.8")
    if not es_short and t_total > 120:
        filtros.append(
            f"drawtext={font}text='Subscribe for daily Ganesha mantras':fontcolor=white:fontsize=54:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:{borde}:"
            f"enable='gt(t,{t_total - 20})':alpha='min(1,(t-{t_total - 20})/2)'")
    filtros.append(f"fade=t=out:st={max(0, t_total - 3)}:d=3")
    return ','.join(filtros)


def montar_video(titulo, duracion=None, es_short=False):
    duracion = duracion or DURACION_LARGO
    t_total = 58 if es_short else int(duracion)
    print(f"Montando {'SHORT' if es_short else 'VIDEO ' + str(t_total//60) + 'min'} HD con transiciones...")
    if not get_musicas():
        print("ERROR: Falta musica")
        return None

    w, h = (1080, 1920) if es_short else (1920, 1080)
    fps = 25
    salida = '/tmp/short.mp4' if es_short else '/tmp/video_final.mp4'
    trabajo = '/tmp/mv_trabajo'
    shutil.rmtree(trabajo, ignore_errors=True)
    os.makedirs(trabajo, exist_ok=True)

    n_clips, por_seg = (14, 14) if es_short else (32, 8)
    segmentos = construir_segmentos(es_short, w, h, fps, trabajo, n_clips, por_seg,
                                    vf_post=GRADE_VIDEO)
    if not segmentos:
        print("ERROR: No se pudo generar ningun segmento de video")
        return None
    print(f"  {len(segmentos)} segmentos de video listos")

    # Secuencia: segmentos barajados, sin repetir el mismo dos veces seguidas
    lista_path = f'{trabajo}/lista.txt'
    acumulado, ultimo = 0.0, None
    with open(lista_path, 'w') as f:
        while acumulado < t_total + 5:
            ciclo = segmentos.copy()
            random.shuffle(ciclo)
            if len(ciclo) > 1 and ciclo[0][0] == ultimo:
                ciclo[0], ciclo[-1] = ciclo[-1], ciclo[0]
            for seg, d in ciclo:
                f.write(f"file '{seg}'\n")
                acumulado += d
                ultimo = seg
                if acumulado >= t_total + 5:
                    break

    mezcla = crear_mezcla_audio(t_total, salida=f'{trabajo}/audio.m4a')
    if mezcla:
        entrada_audio, codec_audio = ['-i', mezcla], ['-c:a', 'copy']
    else:
        musica = random.choice(get_musicas())
        entrada_audio = ['-stream_loop', '-1', '-i', musica]
        codec_audio = ['-c:a', 'aac', '-b:a', '192k']

    titulo_txt = texto_visual(titulo, 60 if es_short else 80)
    vf = filtros_texto(titulo_txt, es_short, t_total)

    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista_path,
           *entrada_audio, '-map', '0:v', '-map', '1:a',
           '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
           '-maxrate', '7M', '-bufsize', '14M',
           '-r', str(fps), '-pix_fmt', 'yuv420p', *codec_audio,
           '-t', str(t_total), '-movflags', '+faststart', salida]
    result = subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(trabajo, ignore_errors=True)

    if os.path.exists(salida) and os.path.getsize(salida) > 100000:
        print(f"  OK HD: {os.path.getsize(salida)//1024//1024}MB")
        return salida
    print(f"  Error: {result.stderr[-600:]}")
    return None


def agregar_capitulos(descripcion, duracion_min, idioma='es'):
    """Capitulos reales (timestamps) para videos largos + pie de pagina."""
    capitulos = ""
    if duracion_min >= 9:
        nombres = ["Opening Mantra", "Deep Focus", "Inner Calm", "Sacred Frequency",
                   "Blessing Flow", "Gratitude", "Abundance Mindset", "Closing Blessing"]
        n = min(len(nombres), max(3, duracion_min // 2))
        paso = (duracion_min * 60) // n
        lineas = []
        for i in range(n):
            seg = i * paso
            lineas.append(f"{seg // 60:02d}:{seg % 60:02d} {nombres[i]}")
        capitulos = "\n\nChapters:\n" + "\n".join(lineas)
    if idioma in ('es', 'pt'):
        footer = "\n\nSuscribete: youtube.com/@SpiritualWave888\n"
        footer += "Activa la campana para recibir mantras cada dia\n\n"
        footer += "La musica, las imagenes y los videos fueron creados con herramientas de inteligencia artificial."
    else:
        footer = "\n\nSubscribe: youtube.com/@SpiritualWave888\n"
        footer += "Turn on the bell to get new mantras every day\n\n"
        footer += "The music, images and videos were created with artificial intelligence tools."
    return descripcion + capitulos + footer


def agregar_a_playlist(youtube, video_id, playlist_nombre):
    try:
        playlists = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
        playlist_id = None
        for pl in playlists.get('items', []):
            if pl['snippet']['title'] == playlist_nombre:
                playlist_id = pl['id']
                break
        if not playlist_id:
            resp = youtube.playlists().insert(
                part='snippet,status',
                body={
                    'snippet': {'title': playlist_nombre, 'description': f'Videos de {playlist_nombre} - SpiritualWave'},
                    'status': {'privacyStatus': 'public'}
                }
            ).execute()
            playlist_id = resp['id']
            print(f"  Playlist creada: {playlist_nombre}")
        youtube.playlistItems().insert(
            part='snippet',
            body={'snippet': {'playlistId': playlist_id, 'resourceId': {'kind': 'youtube#video', 'videoId': video_id}}}
        ).execute()
        print(f"  Agregado a playlist: {playlist_nombre}")
        return True
    except Exception as e:
        print(f"  Playlist error: {e}")
        return False


def generar_srt(titulo, duracion_min, idioma='es'):
    frases_es = [
        "Bienvenido a SpiritualWave. Activa las notificaciones para no perderte nada.",
        "Relaja tu mente y abre tu corazon a las frecuencias sagradas de Ganesha.",
        "Om Gan Ganapataye Namaha. El mantra mas poderoso para eliminar obstaculos.",
        "Respira profundo. Deja que la energia de Ganesha fluya a traves de ti.",
        "Suscribete al canal para recibir mantras poderosos cada dia.",
        "Que Ganesha elimine todos los obstaculos de tu camino hacia la abundancia.",
        "Gracias por acompanarnos en esta practica espiritual. Namaste.",
    ]
    frases_en = [
        "Welcome to SpiritualWave. Turn on notifications so you never miss anything.",
        "Relax your mind and open your heart to Ganesha's sacred frequencies.",
        "Om Gan Ganapataye Namaha. The most powerful mantra to remove obstacles.",
        "Breathe deeply. Let Ganesha's energy flow through you.",
        "Subscribe to the channel to receive powerful mantras every day.",
        "May Ganesha remove all obstacles on your path to abundance.",
        "Thank you for joining us in this spiritual practice. Namaste.",
    ]
    
    frases = frases_en if idioma == 'en' else frases_es
    duracion_seg = duracion_min * 60
    intervalo = duracion_seg // len(frases)
    
    srt = ""
    for i, frase in enumerate(frases):
        inicio = i * intervalo
        fin = inicio + min(intervalo - 2, 30)
        
        h_i, m_i, s_i = inicio//3600, (inicio%3600)//60, inicio%60
        h_f, m_f, s_f = fin//3600, (fin%3600)//60, fin%60
        
        srt += f"{i+1}\n"
        srt += f"{h_i:02d}:{m_i:02d}:{s_i:02d},000 --> {h_f:02d}:{m_f:02d}:{s_f:02d},000\n"
        srt += f"{frase}\n\n"
    
    path = f'/tmp/subtitulos_{idioma}.srt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(srt)
    return path

_HZ_HASHTAG = re.compile(r'#(\d+)\s*[Hh][Zz]\b')
_HZ_TEXTO = re.compile(r'(\d+)\s*[Hh][Zz]\b')


def sin_hz(texto):
    """528Hz / 528 hz -> Frequency 528 (evita titulos y tags con 'hz' que YouTube penaliza)."""
    t = _HZ_HASHTAG.sub(r'#Frequency\1', texto or '')
    return _HZ_TEXTO.sub(r'Frequency \1', t)


def subir_youtube(video_path, titulo, descripcion, tags, es_short=False, duracion_min=60, variante=1, playlist_nombre=None, idioma='es'):
    titulo, descripcion, tags = sin_hz(titulo), sin_hz(descripcion), sin_hz(tags)
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
    desc_final = descripcion if es_short else agregar_capitulos(descripcion, duracion_min, idioma)

    if tags and tags.split()[0] not in desc_final:
        desc_final = desc_final + "\n\n" + tags

    body = {
        'snippet': {
            'title': titulo_final[:100],
            'description': desc_final[:4900],
            'tags': lista_tags(tags),
            'categoryId': '22',
            'defaultLanguage': idioma,
            'defaultAudioLanguage': idioma
        },
        'status': {'privacyStatus': 'public'}
    }

    DETALLE_SUBIDA.clear()
    DETALLE_SUBIDA['mb'] = os.path.getsize(video_path) // 1024 // 1024
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response = youtube.videos().insert(part='snippet,status', body=body, media_body=media).execute()
    video_id = response['id']
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"  SUBIDO: {url}")
    DETALLE_SUBIDA.update(miniatura=False,
                          subtitulos=None if es_short else False,
                          comentario=None if es_short else False,
                          playlist_ok=None if es_short else False)

    if es_short:
        thumb = generar_thumbnail_short(titulo, variante)
        if thumb:
            try:
                youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb, mimetype='image/jpeg')).execute()
                print("  Thumbnail Short OK")
                DETALLE_SUBIDA['miniatura'] = True
            except Exception as e:
                print(f"  Thumbnail Short error: {e}")
    else:
        texto_marca = 'Ganpati Bappa' if idioma == 'hi' else 'SpiritualWave'
        subtexto = {'hi': 'Vighnaharta Ganesha Mantras', 'en': 'Sacred Ganesha Mantras'}.get(idioma, 'Mantras & Frecuencias Divinas')
        thumb = generar_thumbnail(titulo, variante, texto_marca, subtexto)
        if thumb:
            try:
                youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb, mimetype='image/jpeg')).execute()
                print("  Thumbnail OK")
                DETALLE_SUBIDA['miniatura'] = True
            except Exception as e:
                print(f"  Thumbnail error: {e}")

        # Cards desactivadas - API no soportada en version actual

        VIDEOS_SUBIDOS_HOY.append(video_id)

        if playlist_nombre:
            DETALLE_SUBIDA['playlist_ok'] = agregar_a_playlist(youtube, video_id, playlist_nombre)

        # Subtitulos activados
        try:
            srt_path = generar_srt(titulo, duracion_min, idioma)
            if srt_path and os.path.exists(srt_path):
                lang_code = idioma if idioma in ['es', 'en', 'pt'] else 'en'
                lang_name = {'es': 'Español', 'en': 'English', 'pt': 'Português'}.get(lang_code, 'English')
                youtube.captions().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'videoId': video_id,
                            'language': lang_code,
                            'name': lang_name,
                            'isDraft': False
                        }
                    },
                    media_body=MediaFileUpload(srt_path, mimetype='application/octet-stream')
                ).execute()
                print(f"  Subtitulos {lang_name} OK")
                DETALLE_SUBIDA['subtitulos'] = True
        except Exception as e:
            print(f"  Subtitulos error (no critico): {e}")

        try:
            # Comentario fijo neutral para fijar en el video
            comentario_fijo = "Om Gan Ganapataye Namaha. Namaste." if idioma not in ['es', 'pt'] else "Om Gan Ganapataye Namaha. Namaste."
            comment_response = youtube.commentThreads().insert(
                part="snippet",
                body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": comentario_fijo}}}}
            ).execute()
            print("  Comentario fijo publicado")
            DETALLE_SUBIDA['comentario'] = True
        except Exception as e:
            print(f"  Comentario error: {e}")

    return video_id, url

def montar_video_directo(titulo, duracion=6000):
    print(f"Montando video para directo {duracion//60}min...")
    imagenes = get_imagenes()
    musicas = get_musicas(categoria='ambient')
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
                "contentDetails": {"enableAutoStart": True, "enableAutoStop": True, "recordFromStart": True}
            }
        ).execute()
        broadcast_id = broadcast['id']
        print(f"  Broadcast creado: {broadcast_id}")
        stream = youtube.liveStreams().insert(
            part="snippet,cdn",
            body={"snippet": {"title": f"Stream - {titulo[:80]}"}, "cdn": {"frameRate": "30fps", "ingestionType": "rtmp", "resolution": "1080p"}}
        ).execute()
        stream_id = stream['id']
        stream_key = stream['cdn']['ingestionInfo']['streamName']
        rtmp_url = stream['cdn']['ingestionInfo']['ingestionAddress']
        youtube.liveBroadcasts().bind(part="id,contentDetails", id=broadcast_id, streamId=stream_id).execute()
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


TEMAS_SHORTS_HI = [
    "Ganpati Bappa Morya mantra that opens closed doors",
    "Why Vighnaharta removes obstacles before you ask",
    "Om Gan Ganapataye Namaha 21 times and feel the shift",
    "The Ganesha mantra Indian families chant every morning",
    "Shubh Labh Ganesha blessing for money and good luck",
    "What Ganpati Bappa teaches about letting go of fear",
    "Start your day with this Ganesha mantra",
    "Why we chant Ganesha first before anything new",
    "Vakratunda Mahakaya mantra for a fresh beginning",
    "Ganesh mantra for peace when life feels heavy",
    "Listen to this Ganpati chant before an important day",
    "The meaning of Ganpati Bappa Morya most people miss",
]


def generar_hi():
    """Guion del video largo en hindi-ingles (con deteccion de festivales)."""
    festival = detectar_festival_hindu()
    if festival:
        tema = f"Special {festival} Ganesh mantra for blessings prosperity and celebration 2026"
        print(f"\n[VIDEO HI - FESTIVAL: {festival}] {tema}")
    else:
        tema = random.choice(TEMAS_HI)
        print(f"\n[VIDEO HI] {tema}")
    contexto = (f"IMPORTANT: Today is during {festival} celebration, make the title and description "
                f"specifically celebrate this festival with festive greetings.") if festival else ""
    prompt = f"""You are an expert in Hindu spiritual YouTube content for Indian audience.
Generate engaging, honest content for a video about: {tema}
{contexto}
Use English but include devotional Hindi terms like Ganpati Bappa, Vighnaharta, Shubh, Mangal when natural.
Do not make health claims or guaranteed-result promises.
No asterisks, no markdown, no emojis in the title.
Reply EXACTLY in this format:
TITULO: [title maximum 70 characters, impactful, include Ganpati or Ganesha]
DESCRIPCION: [300 words with devotional keywords, benefits of mantra practice, CTA to subscribe to youtube.com/@SpiritualWave888. End with: "The music, images and videos were created with artificial intelligence tools."]
TAGS: [5 hashtags separated by spaces including Ganpati and Ganesha]"""
    base_tags = "#Ganpati #Ganesha #Mantra #Vighnaharta #SpiritualWave"
    try:
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openai/gpt-oss-120b', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 1800},
            timeout=40)
        data = r.json()
        if 'choices' not in data:
            raise RuntimeError(str(data)[:200])
        contenido = data['choices'][0]['message']['content']
        titulo = limpiar_texto(extraer_campo(contenido, 'TITULO', 'DESCRIPCION') or tema[:70])
        desc = limpiar_texto(extraer_campo(contenido, 'DESCRIPCION', 'TAGS') or desc_fallback(tema, 'en'))
        tags = limpiar_texto(extraer_campo(contenido, 'TAGS') or base_tags)
    except Exception as e:
        print(f"Groq HI error: {e}")
        titulo, desc, tags = tema[:70], desc_fallback(tema, 'en'), base_tags
    return titulo[:95].strip(), desc, tags


def producir_largo(idioma):
    """Video horizontal largo. Devuelve dict con titulo, url y detalles de la subida."""
    if idioma == 'hi':
        titulo, desc, tags = generar_hi()
        playlist = "Ganpati Bappa Mantras"
    else:
        tema = random.choice(TEMAS_EN)
        print(f"\n[VIDEO EN] {tema}")
        titulo, desc, tags = generar_guion(tema, 'en')
        playlist = "Ganesha Mantras English"
    video = montar_video(titulo, duracion=DURACION_LARGO) or montar_video(titulo, duracion=DURACION_LARGO)
    if not video:
        raise RuntimeError("No se pudo montar el video largo (2 intentos)")
    _, url = subir_youtube(video, titulo, desc, tags, duracion_min=DURACION_LARGO // 60,
                           variante=random.randint(0, 9), playlist_nombre=playlist, idioma=idioma)
    return {**DETALLE_SUBIDA, 'titulo': titulo, 'url': url, 'duracion': f"{DURACION_LARGO // 60} min",
            'playlist': playlist}


def producir_short(idioma):
    """Short vertical. Devuelve dict con titulo, url y detalles de la subida."""
    temas = TEMAS_SHORTS_HI if idioma == 'hi' else TEMAS_SHORTS_EN
    tema = random.choice(temas)
    print(f"\n[SHORT {idioma.upper()}] {tema}")
    short = montar_video(tema, es_short=True) or montar_video(tema, es_short=True)
    if not short:
        raise RuntimeError("No se pudo montar el short (2 intentos)")
    hashtags = ("#Ganpati #Ganesha #Shorts #Mantra #Bhakti #SpiritualWave" if idioma == 'hi'
                else "#Ganesha #Shorts #Mantra #Spiritual #Meditation #SpiritualWave")
    desc = (f"{tema}\n\nSubscribe: youtube.com/@SpiritualWave888\n\n{hashtags}\n\n"
            "The music, images and videos were created with artificial intelligence tools.")
    _, url = subir_youtube(short, tema, desc, hashtags, es_short=True,
                           variante=random.randint(0, 9), idioma=idioma)
    return {**DETALLE_SUBIDA, 'titulo': tema, 'url': url, 'duracion': '58 s'}


def main():
    t0 = time.time()
    idioma = (os.environ.get('RUN_IDIOMA') or '').strip().lower()
    if idioma not in ('en', 'hi'):
        # 14:00 UTC (19:30 India) -> hindi, 22:00 UTC (18:00 Nueva York) -> ingles
        idioma = 'hi' if 10 <= datetime.utcnow().hour < 18 else 'en'
    print(f"=== SPIRITUALWAVE PRODUCER | idioma de esta ejecucion: {idioma} ===")

    verificar_salud()
    notificar.produccion_iniciada(
        idioma, [f"\U0001F3AC Video largo de {DURACION_LARGO // 60} min", "\U0001F4F1 Short de 1 min"],
        estimado_min=25)

    resultados, errores = [], []
    for nombre, tipo, funcion in (("Video largo", 'largo', producir_largo), ("Short", 'short', producir_short)):
        try:
            d = funcion(idioma)
            resultados.append((nombre, d['titulo'], d['url']))
            notificar.video_subido(
                tipo, idioma, d['titulo'], d['url'], duracion=d.get('duracion'), mb=d.get('mb'),
                playlist=d.get('playlist') if d.get('playlist_ok') else None,
                miniatura=d.get('miniatura'), subtitulos=d.get('subtitulos'), comentario=d.get('comentario'))
        except Exception as e:
            errores.append(f"{nombre}: {str(e)[:120]}")
            print(f"ERROR en {nombre}: {e}")
            notificar.error(nombre, e, idioma)

    notificar.resumen_ejecucion(idioma, resultados, errores, time.time() - t0)
    print("\n=== PROCESO FINALIZADO ===")
    if not resultados:
        # Que el workflow quede en ROJO si no se produjo nada
        sys.exit(1)


if __name__ == '__main__':
    main()
