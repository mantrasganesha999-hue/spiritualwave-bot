content = open('scripts/pipeline_cloud.py', encoding='utf-8').read()

old = 'def agregar_capitulos(descripcion, duracion_min):'

if old in content:
    # Encontrar y reemplazar la funcion completa
    inicio = content.index(old)
    fin = content.index('\ndef ', inicio + 1)
    
    nueva_funcion = '''def agregar_capitulos(descripcion, duracion_min):
    caps = "\\n\\nCAPITULOS:\\n"
    caps += "00:00 - Introduccion y bienvenida\\n"
    caps += "00:30 - Mantra principal Om Gan Ganapataye Namaha\\n"
    paso = duracion_min // 5
    temas = [
        "Meditacion profunda con frecuencias sagradas",
        "Afirmaciones de abundancia y prosperidad",
        "Sanacion energetica y limpieza del aura",
        "Cierre y bendicion de Ganesha"
    ]
    tiempos = [paso, paso*2, paso*3, paso*4]
    for tiempo, tema in zip(tiempos, temas):
        h = tiempo // 60
        m = tiempo % 60
        if h > 0:
            caps += f"{h:01d}:{m:02d}:00 - {tema}\\n"
        else:
            caps += f"{m:02d}:00 - {tema}\\n"
    if VIDEOS_SUBIDOS_HOY:
        caps += f"\\nContinua tu practica espiritual con nuestro video anterior:\\n"
        caps += f"https://www.youtube.com/watch?v={VIDEOS_SUBIDOS_HOY[-1]}\\n"
    caps += "\\nSuscribete: youtube.com/@SpiritualWave888\\n"
    caps += "Activa la campana para no perderte nada\\n"
    return descripcion + caps
'''
    
    content = content[:inicio] + nueva_funcion + content[fin:]
    open('scripts/pipeline_cloud.py', 'w', encoding='utf-8').write(content)
    print('Timestamps reales aplicados OK')
else:
    print('Funcion no encontrada')