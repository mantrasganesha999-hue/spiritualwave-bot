"""Casting de voces en hindi: genera el mismo parrafo con varias voces para escucharlas y elegir.
Uso (PowerShell, desde C:\\SpiritualWave):  python scripts\\v3\\casting_voces.py
Opcional ElevenLabs: antes de correrlo,  $env:ELEVENLABS_API_KEY="tu_clave"
Deja los audios en C:\\SpiritualWave\\casting\\ y abre la carpeta."""
import os, sys, asyncio, subprocess, requests
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, 'casting'); os.makedirs(OUT, exist_ok=True)
TEXTO = ("बहुत समय पहले की बात है। हिमालय की ऊँची, बर्फ से ढकी चोटियों के बीच, कैलाश पर्वत पर, भगवान शिव और माता पार्वती "
         "निवास करते थे। आज हम शिव पुराण में बताई गई, गणेश जी के जन्म की कथा सुनेंगे। ॐ गं गणपतये नमः।")
hechos = []
try:
    import edge_tts
    async def edge(voz, rate, nombre):
        await edge_tts.Communicate(TEXTO, voz, rate=rate).save(os.path.join(OUT, nombre))
    for voz, rate, nombre in (('hi-IN-MadhurNeural', '-6%', 'microsoft_madhur_hombre.mp3'),
                              ('hi-IN-MadhurNeural', '-14%', 'microsoft_madhur_hombre_lento.mp3'),
                              ('hi-IN-SwaraNeural', '-6%', 'microsoft_swara_mujer.mp3'),
                              ('hi-IN-SwaraNeural', '-14%', 'microsoft_swara_mujer_lento.mp3')):
        asyncio.run(edge(voz, rate, nombre)); hechos.append(nombre)
except Exception as e:
    print("Microsoft (Edge) no disponible:", e, "-> instala con: python -m pip install edge-tts")
key = os.environ.get('ELEVENLABS_API_KEY')
if key:
    try:
        voces = requests.get('https://api.elevenlabs.io/v1/voices', headers={'xi-api-key': key}, timeout=60).json().get('voices', [])
        for v in voces[:6]:
            r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{v['voice_id']}?output_format=mp3_44100_128",
                              headers={'xi-api-key': key}, json={'text': TEXTO, 'model_id': 'eleven_multilingual_v2'}, timeout=180)
            if r.status_code == 200:
                n = f"elevenlabs_{v['name'].replace(' ', '_')}__{v['voice_id']}.mp3"
                open(os.path.join(OUT, n), 'wb').write(r.content); hechos.append(n)
            else:
                print("ElevenLabs", v['name'], r.status_code, r.text[:120])
    except Exception as e:
        print("ElevenLabs error:", e)
else:
    print("(Sin ELEVENLABS_API_KEY: solo se generan las voces de Microsoft)")
print("\nVoces generadas:"); [print("  ", h) for h in hechos]
print(f"\nCarpeta: {OUT}")
if os.name == 'nt':
    subprocess.Popen(['explorer', OUT])
