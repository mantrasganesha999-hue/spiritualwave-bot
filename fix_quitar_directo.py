content = open('scripts/pipeline_cloud.py', encoding='utf-8').read()

old = """try:
    titulo_live = "🔱 Ganesha 528Hz Live - Musica Espiritual - SpiritualWave"
    desc_live = "Transmision en vivo de musica espiritual con mantras de Ganesha y frecuencias 528hz.\\n\\nSuscribete: youtube.com/@SpiritualWave888\\n\\n#Ganesha #Live #528hz #Meditacion"
    telegram(f"🔴 <b>Iniciando transmision en vivo</b>\\n📅 {fecha}\\n⏳ Duracion: ~1.5 horas")
    video_live = montar_video_directo(titulo_live, duracion=6000)
    if video_live:
        broadcast_id = crear_directo_youtube(titulo_live, desc_live, video_live)
        if broadcast_id:
            telegram(f"🔴 <b>Directo finalizado</b>\\n🔗 https://www.youtube.com/watch?v={broadcast_id}")
        else:
            telegram("⚠️ El directo fallo pero los videos ya se subieron correctamente")
    else:
        telegram("⚠️ No se pudo generar el video para el directo")
except Exception as e:
    telegram(f"⚠️ <b>Error en el directo (no afecta videos ya subidos)</b>\\n{str(e)[:200]}")
    print(f"Error directo: {e}")"""

new = """# Directo movido a workflow separado para conservar quota de API"""

if old in content:
    content = content.replace(old, new)
    open('scripts/pipeline_cloud.py', 'w', encoding='utf-8').write(content)
    print('Directo removido del pipeline principal OK')
else:
    print('Bloque no encontrado - verificar manualmente')