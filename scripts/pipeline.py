import requests, subprocess, os, random, sys
from gtts import gTTS

GROQ_KEY = "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"

IMAGENES = {
    "espiritual": [
        "C:/SpiritualWave/assets/backgrounds/ganesha_1.jpg",
        "C:/SpiritualWave/assets/backgrounds/ganesha_2.jpg",
        "C:/SpiritualWave/assets/backgrounds/ganesha_3.jpg",
        "C:/SpiritualWave/assets/backgrounds/ganesha_4.jpg",
        "C:/SpiritualWave/assets/backgrounds/ganesha_5.jpg",
    ],
    "finanzas": [
        "C:/SpiritualWave/assets/backgrounds/ganesha_1.jpg",
        "C:/SpiritualWave/assets/backgrounds/ganesha_3.jpg",
        "C:/SpiritualWave/assets/backgrounds/ganesha_4.jpg",
    ]
}

TEMAS = [
    ("mantra de Ganesha para atraer abundancia y eliminar deudas", "espiritual"),
    ("frecuencias 528hz para sanar el cuerpo y atraer prosperidad", "espiritual"),
    ("afirmaciones poderosas para manifestar dinero cada manana", "finanzas"),
    ("meditacion guiada para eliminar energia negativa y atraer exito", "espiritual"),
    ("ley de atraccion para atraer dinero abundancia y salud", "finanzas"),
    ("mantra poderoso de Shiva para proteccion y abundancia", "espiritual"),
    ("tecnica de manifestacion de 369 para atraer dinero rapido", "finanzas"),
    ("musica de sanacion 432hz para dormir y restaurar el alma", "espiritual"),
]

def generar_guion(tema):
    print(f"[1/3] Generando guion...")
    prompt = f"""Eres experto en contenido espiritual de YouTube en espanol latino.
Genera contenido viral para un video sobre: {tema}

Responde exactamente en este formato sin caracteres especiales ni tildes:
TITULO: [titulo SEO impactante maximo 65 caracteres sin emojis ni tildes]
DESCRIPCION: [descripcion de 250 palabras con keywords espirituales sin tildes]
TAGS: [25 hashtags separados por espacios]"""

    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 1000}
    )
    return r.json()['choices'][0]['message']['content']

def montar_video_pro(imagenes, musica, titulo, numero):
    print(f"[2/3] Montando video con imagenes cambiantes...")
    salida = f'C:/SpiritualWave/outputs/video_{numero}.mp4'
    titulo_clean = titulo[:55].replace("'", "").replace('"', '').replace(':', '-')

    lista_path = f'C:/SpiritualWave/temp/lista_{numero}.txt'
    with open(lista_path, 'w') as f:
        for _ in range(3):
            for img in imagenes:
                f.write(f"file '{img}'\n")
                f.write(f"duration 10\n")
        f.write(f"file '{imagenes[0]}'\n")

    filtro = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
        "format=yuv420p,"
        f"drawtext=text='{titulo_clean}':fontcolor=white:fontsize=52:"
        "x=(w-text_w)/2:y=h-100:"
        "shadowcolor=0x000000CC:shadowx=3:shadowy=3,"
        "drawtext=text='SpiritualWave':fontcolor=0xFFD700:fontsize=26:"
        "x=(w-text_w)/2:y=35:shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", lista_path,
        "-stream_loop", "-1", "-i", musica,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac", "-b:a", "192k",
        "-t", "300",
        "-vf", filtro,
        "-preset", "fast", "-crf", "20",
        salida
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    return salida

def pipeline_completo(numero=1, tema=None, tipo=None):
    if not tema:
        tema, tipo = random.choice(TEMAS)

    print(f"\n{'='*55}")
    print(f"VIDEO #{numero} — {tema[:50]}")
    print(f"{'='*55}")

    contenido = generar_guion(tema)

    titulo = contenido.split('TITULO:')[1].split('\n')[0].strip()
    descripcion = contenido.split('DESCRIPCION:')[1].split('TAGS:')[0].strip()
    tags = contenido.split('TAGS:')[1].strip()

    with open(f'C:/SpiritualWave/outputs/metadata_{numero}.txt', 'w', encoding='utf-8') as f:
        f.write(f"TITULO: {titulo}\n\nDESCRIPCION: {descripcion}\n\nTAGS: {tags}")

    imagenes = IMAGENES.get(tipo or "espiritual", IMAGENES["espiritual"])
    musica = random.choice([f"C:/SpiritualWave/assets/music/suno_{i}.mp3" for i in range(1, 22)])
    video = montar_video_pro(imagenes, musica, titulo, numero)

    size = os.path.getsize(video) // (1024*1024)
    print(f"\n✅ VIDEO #{numero} LISTO ({size}MB)")
    print(f"   Titulo: {titulo}")
    return video

num = int(sys.argv[1]) if len(sys.argv) > 1 else 8
pipeline_completo(numero=num)