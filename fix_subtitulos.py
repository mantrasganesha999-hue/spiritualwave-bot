content = open('scripts/pipeline_cloud.py', encoding='utf-8').read()

# Agregar funcion de subtitulos justo antes de subir_youtube
nueva_funcion = '''
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
        
        srt += f"{i+1}\\n"
        srt += f"{h_i:02d}:{m_i:02d}:{s_i:02d},000 --> {h_f:02d}:{m_f:02d}:{s_f:02d},000\\n"
        srt += f"{frase}\\n\\n"
    
    path = f'/tmp/subtitulos_{idioma}.srt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(srt)
    return path

'''

# Insertar antes de def subir_youtube
if 'def subir_youtube(' in content:
    idx = content.index('def subir_youtube(')
    content = content[:idx] + nueva_funcion + content[idx:]
    
    # Agregar llamada a subtitulos dentro de subir_youtube, despues de subir thumbnail
    old = '''        if playlist_nombre:
            agregar_a_playlist(youtube, video_id, playlist_nombre)'''
    new = '''        if playlist_nombre:
            agregar_a_playlist(youtube, video_id, playlist_nombre)

        try:
            srt_path = generar_srt(titulo, duracion_min, idioma)
            youtube.captions().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'language': idioma,
                        'name': 'SpiritualWave',
                        'isDraft': False
                    }
                },
                media_body=__import__('googleapiclient.http', fromlist=['MediaFileUpload']).MediaFileUpload(
                    srt_path, mimetype='application/octet-stream'
                )
            ).execute()
            print(f"  Subtitulos {idioma} OK")
        except Exception as e:
            print(f"  Subtitulos error: {e}")'''
    
    content = content.replace(old, new)
    open('scripts/pipeline_cloud.py', 'w', encoding='utf-8').write(content)
    print('Subtitulos automaticos OK')
else:
    print('No encontrado')