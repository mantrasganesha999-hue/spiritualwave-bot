content = open('scripts/pipeline_cloud.py', encoding='utf-8').read()

# Quitar subtitulos (muy costoso en quota, poco impacto visible)
old = """        try:
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
            print(f"  Subtitulos error: {e}")"""

new = """        # Subtitulos desactivados para conservar quota de API"""

if old in content:
    content = content.replace(old, new)
    print('Subtitulos desactivados OK')
else:
    print('Subtitulos no encontrados - ya pueden estar desactivados')

# Quitar cards (no soportada en esta version de API)
old2 = """        if VIDEOS_SUBIDOS_HOY:
            try:
                video_anterior = VIDEOS_SUBIDOS_HOY[-1]
                youtube.cards().insert(
                    videoId=video_id,
                    body={"card": {"videoIdCard": {"videoId": video_anterior}}}
                ).execute()
                print("  Card OK")
            except Exception as e:
                print(f"  Card error: {e}")"""

new2 = """        # Cards desactivadas - API no soportada en version actual"""

if old2 in content:
    content = content.replace(old2, new2)
    print('Cards desactivadas OK')
else:
    print('Cards no encontradas - ya pueden estar desactivadas')

open('scripts/pipeline_cloud.py', 'w', encoding='utf-8').write(content)
print('Fix quota completado')