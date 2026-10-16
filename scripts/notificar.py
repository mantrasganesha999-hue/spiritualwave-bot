"""Notificaciones de Telegram de SpiritualWave: un solo formato para todo el canal.

- Todos los scripts usan este modulo (antes cada uno tenia su propio telegram()).
- El texto dinamico se escapa (un titulo con < o & ya no rompe el mensaje).
- Si Telegram rechaza el HTML, se reenvia en texto plano (nunca se pierde el aviso).
- Reintenta ante errores de red / limite de velocidad y deja el motivo en el log.
"""
import os, re, html, time, requests
from datetime import datetime, timedelta, timezone

LINEA = "━━━━━━━━━━━━━━━━━━━━"
MAX_CHARS = 3800
IDIOMAS = {'en': '🇺🇸 Inglés', 'hi': '🇮🇳 Hindi', 'es': '🇪🇸 Español', 'pt': '🇧🇷 Portugués'}
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


# ---------------------------------------------------------------- utilidades
def esc(texto):
    return html.escape('' if texto is None else str(texto), quote=False)


def ahora_co():
    return datetime.now(timezone.utc) + timedelta(hours=-5)  # Colombia no tiene horario de verano


def fecha_hora():
    d = ahora_co()
    return f"{d.day} {MESES[d.month - 1]} {d.year} · {d:%H:%M} (Colombia)"


def url_run():
    server = os.environ.get('GITHUB_SERVER_URL')
    repo = os.environ.get('GITHUB_REPOSITORY')
    run = os.environ.get('GITHUB_RUN_ID')
    if server and repo and run:
        return f"{server}/{repo}/actions/runs/{run}"
    return None


def campo(emoji, etiqueta, valor):
    if valor is None or valor == '':
        return None
    return f"{emoji} <b>{esc(etiqueta)}:</b> {esc(valor)}"


def marca(flag):
    return None if flag is None else ('✅' if flag else '❌')


def duracion_txt(segundos):
    segundos = int(segundos)
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h} h {m:02d} min"
    if m:
        return f"{m} min {s:02d} s"
    return f"{s} s"


# ------------------------------------------------------------------- envio
def _credenciales():
    return os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHAT_ID')


def _trozos(texto):
    if len(texto) <= MAX_CHARS:
        return [texto]
    trozos, actual = [], ''
    for linea in texto.split('\n'):
        if len(actual) + len(linea) + 1 > MAX_CHARS and actual:
            trozos.append(actual)
            actual = ''
        actual += linea + '\n'
    if actual.strip():
        trozos.append(actual.rstrip('\n'))
    return trozos


def _post(token, payload):
    r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json=payload, timeout=15)
    try:
        data = r.json()
    except ValueError:
        data = {}
    return r.status_code, data


def enviar(texto, botones=None, silencioso=False, preview=False):
    """Envia un mensaje HTML. botones = [(texto, url), ...]. Devuelve True si llego."""
    token, chat = _credenciales()
    if not token or not chat:
        print("  [Telegram] no configurado (faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False
    trozos = _trozos(texto)
    ok_total = True
    for i, trozo in enumerate(trozos):
        payload = {'chat_id': chat, 'text': trozo, 'parse_mode': 'HTML',
                   'disable_web_page_preview': not preview, 'disable_notification': bool(silencioso)}
        if botones and i == len(trozos) - 1:
            payload['reply_markup'] = {'inline_keyboard': [[{'text': t, 'url': u}] for t, u in botones if u]}
        enviado = False
        for intento in range(1, 4):
            try:
                status, data = _post(token, payload)
            except Exception as e:
                print(f"  [Telegram] error de red (intento {intento}): {e}")
                time.sleep(2 * intento)
                continue
            if status == 200:
                enviado = True
                break
            descripcion = data.get('description', '')
            if status == 429:
                espera = data.get('parameters', {}).get('retry_after', 3)
                time.sleep(min(int(espera) + 1, 30))
                continue
            if status == 400 and 'parse' in descripcion.lower():
                print(f"  [Telegram] HTML rechazado ({descripcion}); reenviando en texto plano")
                payload['text'] = html.unescape(re.sub(r'<[^>]+>', '', trozo))
                payload.pop('parse_mode', None)
                continue
            print(f"  [Telegram] error {status}: {descripcion}")
            break
        ok_total = ok_total and enviado
    return ok_total


def mensaje(icono, titulo, lineas=(), botones=None, silencioso=False, preview=False, pie=True):
    cuerpo = f"{icono} <b>{esc(titulo)}</b>\n{LINEA}\n"
    cuerpo += "\n".join(l for l in lineas if l is not None)
    if pie:
        cuerpo += f"\n{LINEA}\n🕐 {fecha_hora()}"
    return enviar(cuerpo, botones=botones, silencioso=silencioso, preview=preview)


# ----------------------------------------------------------- avisos listos
def produccion_iniciada(idioma, plan, estimado_min=None):
    lineas = [campo('🌐', 'Idioma de esta ejecución', IDIOMAS.get(idioma, idioma)), "", "📋 <b>Plan</b>"]
    lineas += [f"   ▫️ {esc(p)}" for p in plan]
    if estimado_min:
        lineas += ["", f"⏳ Tiempo estimado: ~{estimado_min} min"]
    return mensaje('🚀', 'PRODUCCIÓN INICIADA', lineas, botones=[('🔍 Ver progreso en GitHub', url_run())],
                   silencioso=True)


TIPOS_VIDEO = {
    'largo': ('🎬', 'VIDEO LARGO SUBIDO'),
    'short': ('📱', 'SHORT SUBIDO'),
    'sleep': ('🌙', 'SLEEP MUSIC SUBIDO'),
}


def video_subido(tipo, idioma, titulo, url, duracion=None, mb=None, playlist=None,
                 miniatura=None, subtitulos=None, comentario=None):
    icono, encabezado = TIPOS_VIDEO.get(tipo, ('🎬', 'VIDEO SUBIDO'))
    lineas = [f"📌 <b>{esc(titulo)}</b>", "",
              campo('🌐', 'Idioma', IDIOMAS.get(idioma, idioma)) if idioma else None,
              campo('⏱', 'Duración', duracion),
              campo('📦', 'Tamaño', f"{mb} MB" if mb else None),
              campo('📚', 'Playlist', playlist)]
    chequeos = [f"{n} {marca(v)}" for n, v in (('🖼 Miniatura', miniatura), ('💬 Subtítulos', subtitulos),
                                              ('📝 Comentario', comentario)) if v is not None]
    if chequeos:
        lineas += ["", " · ".join(chequeos)]
    lineas += ["", f"🔗 {esc(url)}"]
    return mensaje(icono, encabezado, lineas, botones=[('▶️ Ver en YouTube', url)])


PISTAS_ERROR = [
    ('quotaExceeded', "La cuota diaria de la API de YouTube se agotó. Se reinicia a las 2:00 am (hora Colombia). "
                      "El siguiente ciclo sube con normalidad; no hace falta actuar."),
    ('uploadLimitExceeded', "YouTube alcanzó el límite de subidas del canal por hoy. Se libera en unas 24 h."),
    ('invalid_grant', "El token de YouTube venció o fue revocado. Genera uno nuevo (renovar_token_auto.py) "
                      "y actualiza el secreto YOUTUBE_TOKEN en GitHub."),
    ('Token has been expired', "El token de YouTube venció. Genera uno nuevo y actualiza el secreto YOUTUBE_TOKEN."),
    ('liveStreamingNotEnabled', "El canal no tiene los directos habilitados. Actívalos en YouTube Studio "
                                "(puede tardar 24 h en activarse)."),
    ('mezcla de audio', "Revisa que la carpeta assets/music tenga archivos .mp3."),
    ('rateLimitExceeded', "YouTube pidió ir más despacio. Se reintenta en el próximo ciclo."),
]


def error(proceso, detalle, idioma=None, pista=None):
    detalle = str(detalle)
    if pista is None:
        for patron, texto in PISTAS_ERROR:
            if patron.lower() in detalle.lower():
                pista = texto
                break
    lineas = [campo('🧩', 'Proceso', proceso),
              campo('🌐', 'Idioma', IDIOMAS.get(idioma, idioma)) if idioma else None,
              "", f"<code>{esc(detalle[:350])}</code>"]
    if pista:
        lineas += ["", f"💡 <b>Qué hacer:</b> {esc(pista)}"]
    return mensaje('🚨', 'ERROR', lineas, botones=[('🔍 Ver log del workflow', url_run())])


def resumen_ejecucion(idioma, resultados, errores, segundos):
    """resultados = [(nombre, titulo, url)], errores = [texto]"""
    if resultados and not errores:
        icono, titulo = '✅', 'EJECUCIÓN COMPLETA'
    elif resultados:
        icono, titulo = '⚠️', 'EJECUCIÓN PARCIAL'
    else:
        icono, titulo = '🚨', 'EJECUCIÓN FALLIDA'
    lineas = [campo('🌐', 'Idioma', IDIOMAS.get(idioma, idioma)),
              campo('⏱', 'Duración total', duracion_txt(segundos)), ""]
    for nombre, tit, _ in resultados:
        lineas.append(f"✅ <b>{esc(nombre)}:</b> {esc(tit[:70])}")
    for err in errores:
        lineas.append(f"❌ {esc(err[:120])}")
    botones = [(f"▶️ {n}", u) for n, _, u in resultados]
    botones.append(('🔍 Ver log del workflow', url_run()))
    return mensaje(icono, titulo, lineas, botones=botones)


def salud(problemas):
    lineas = [f"❌ {esc(p)}" for p in problemas]
    lineas += ["", "💡 <b>Qué hacer:</b> corrige esto antes de la próxima ejecución."]
    return mensaje('🩺', 'CHEQUEO DE SALUD: HAY PROBLEMAS', lineas,
                   botones=[('🔍 Ver log del workflow', url_run())])


def directo_preparando(titulo, horas):
    lineas = [f"📌 <b>{esc(titulo)}</b>", "",
              campo('⏱', 'Duración planeada', f"{horas:g} h"),
              "🛠 Preparando video en bucle y audio (~12 min)..."]
    return mensaje('📡', 'PREPARANDO DIRECTO', lineas, silencioso=True,
                   botones=[('🔍 Ver progreso en GitHub', url_run())])


def directo_en_vivo(titulo, url):
    lineas = [f"📌 <b>{esc(titulo)}</b>", "", "El directo ya está transmitiendo. 🙏", "", f"🔗 {esc(url)}"]
    return mensaje('🔴', 'EN VIVO AHORA', lineas, botones=[('▶️ Abrir el directo', url)])


def directo_sin_vivo(estado, url):
    lineas = [campo('📍', 'Estado actual', estado), "",
              "Pasaron 3 min y YouTube aún no lo marca como 'en vivo'. Revisa YouTube Studio → Directos.",
              "", f"🔗 {esc(url)}"]
    return mensaje('⚠️', 'EL DIRECTO NO ARRANCÓ AÚN', lineas, botones=[('🔧 Abrir YouTube Studio', 'https://studio.youtube.com')])


def directo_progreso(transcurrido_s, total_s, espectadores=None):
    pct = int(100 * transcurrido_s / total_s) if total_s else 0
    llenos = max(0, min(10, pct // 10))
    barra = '🟥' * llenos + '⬜' * (10 - llenos)
    lineas = [f"{barra} {pct}%", "",
              campo('⏱', 'Transcurrido', f"{duracion_txt(transcurrido_s)} de {duracion_txt(total_s)}"),
              campo('👥', 'Espectadores ahora', espectadores)]
    return mensaje('📊', 'DIRECTO EN CURSO', lineas, silencioso=True)


def directo_finalizado(titulo, url, segundos):
    lineas = [f"📌 <b>{esc(titulo)}</b>", "",
              campo('⏱', 'Duración', duracion_txt(segundos)),
              "La grabación queda disponible como video en tu canal.", "", f"🔗 {esc(url)}"]
    return mensaje('✅', 'DIRECTO FINALIZADO', lineas, botones=[('▶️ Ver la grabación', url)])


def comentarios(respondidos, errores, revisados=None):
    icono = '💬' if not errores else '⚠️'
    lineas = [campo('👀', 'Comentarios revisados', revisados),
              campo('✅', 'Respondidos', respondidos),
              campo('❌', 'Con error', errores)]
    if not respondidos and not errores:
        lineas.append("😴 No había comentarios nuevos que responder.")
    return mensaje(icono, 'COMENTARIOS', lineas, silencioso=(respondidos == 0 and not errores))


def post_comunidad(texto):
    lineas = ["Toca el texto para copiarlo y pégalo en la pestaña Comunidad:", "",
              f"<code>{esc(texto)}</code>", "",
              "📍 YouTube Studio → Contenido → Publicaciones → Crear"]
    return mensaje('📢', 'POST SUGERIDO PARA COMUNIDAD', lineas,
                   botones=[('📮 Abrir YouTube Studio', 'https://studio.youtube.com')])
