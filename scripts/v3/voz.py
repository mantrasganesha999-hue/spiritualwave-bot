"""Voz automatica en hindi. Orden: archivo propio (voz/NN.mp3) > ElevenLabs > Azure > Microsoft Edge (gratis)."""
import os, asyncio, html, requests

def motor():
    m = (os.environ.get('VOZ_MOTOR') or '').strip().lower()
    if m:
        return m
    if os.environ.get('ELEVENLABS_API_KEY'):
        return 'elevenlabs'
    if os.environ.get('AZURE_SPEECH_KEY'):
        return 'azure'
    return 'edge'

VOZ_EDGE = os.environ.get('VOZ_EDGE') or 'hi-IN-MadhurNeural'      # masculina calmada; alternativa: hi-IN-SwaraNeural
VOZ_AZURE = os.environ.get('VOZ_AZURE') or 'hi-IN-MadhurNeural'

def _elevenlabs(texto, salida):
    vid = os.environ.get('ELEVENLABS_VOICE_ID')
    if not vid:
        raise RuntimeError("falta ELEVENLABS_VOICE_ID")
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                      headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY'], 'Content-Type': 'application/json'},
                      json={'text': texto, 'model_id': os.environ.get('ELEVENLABS_MODEL') or 'eleven_multilingual_v2',
                            'voice_settings': {'stability': 0.55, 'similarity_boost': 0.8, 'style': 0.15}},
                      timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
    open(salida, 'wb').write(r.content)

def _azure(texto, salida, rate='-6%'):
    region = os.environ.get('AZURE_SPEECH_REGION') or 'centralindia'
    ssml = (f"<speak version='1.0' xml:lang='hi-IN'><voice name='{VOZ_AZURE}'><prosody rate='{rate}'>"
            f"{html.escape(texto)}</prosody></voice></speak>")
    r = requests.post(f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                      headers={'Ocp-Apim-Subscription-Key': os.environ['AZURE_SPEECH_KEY'],
                               'Content-Type': 'application/ssml+xml',
                               'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3',
                               'User-Agent': 'spiritualwave'}, data=ssml.encode('utf-8'), timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"Azure {r.status_code}: {r.text[:200]}")
    open(salida, 'wb').write(r.content)

def _edge(texto, salida, rate='-6%'):
    import edge_tts
    async def go():
        await edge_tts.Communicate(texto, VOZ_EDGE, rate=rate).save(salida)
    asyncio.run(go())

def generar(texto, salida, rate='-6%'):
    """Genera salida (mp3) si no existe. Devuelve el motor usado ('propia' si ya existia)."""
    if os.path.exists(salida) and os.path.getsize(salida) > 1000:
        return 'propia'
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    m = motor()
    orden = [m] + [x for x in ('elevenlabs', 'azure', 'edge') if x != m]
    ultimo = None
    for mm in orden:
        if mm == 'elevenlabs' and not os.environ.get('ELEVENLABS_API_KEY'):
            continue
        if mm == 'azure' and not os.environ.get('AZURE_SPEECH_KEY'):
            continue
        for intento in range(3):
            try:
                {'elevenlabs': _elevenlabs, 'azure': lambda t, s: _azure(t, s, rate), 'edge': lambda t, s: _edge(t, s, rate)}[mm](texto, salida)
                if os.path.getsize(salida) > 1000:
                    return mm
            except Exception as e:
                ultimo = e
    raise RuntimeError(f"No se pudo generar la voz: {ultimo}")
