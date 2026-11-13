"""Produccion v3 (GitHub Actions). Busca en contenido/ los videos listos (guion + imagenes), genera la voz,
monta el video, crea la portada y lo sube a YouTube EN PRIVADO Y PROGRAMADO para su fecha. Avisa por Telegram.
Uno por ejecucion (cuota). Un video ya subido tiene contenido/<id>/subido.json y no se repite."""
import os, sys, json, glob, base64, pickle, shutil, traceback
from datetime import datetime, timezone, timedelta
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image
import montaje, voz, portadas_v3 as pv
try:
    import notificar
except Exception:
    notificar = None

BASE = montaje.BASE
SOLO = (os.environ.get('CARPETA') or '').strip()
PERMITIR_BANCO = (os.environ.get('PERMITIR_BANCO') or '') == '1'
PLAYLISTS = {'katha': 'गणेश जी की कथाएँ | Ganesh Katha', 'mantra': 'गणेश मंत्र 108 जाप | Mantra Jaap',
             'chaturthi': 'चतुर्थी व्रत और पूजा विधि', 'aarti': 'गणेश आरती अर्थ सहित'}

def avisar(txt):
    print(txt)
    try:
        if notificar:
            notificar.enviar(txt)
    except Exception as e:
        print("Telegram:", e)

def youtube():
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    creds = pickle.loads(base64.b64decode(os.environ['YOUTUBE_TOKEN']))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)

def faltantes(carpeta, g):
    falta = []
    for e in g['escenas']:
        if e.get('tipo', 'escena') == 'silencio' and not e.get('usa_imagen', True):
            continue
        if not any(os.path.exists(os.path.join(carpeta, 'imagenes', f"{e['n']:02d}.{x}")) for x in ('png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov', 'webm', 'm4v')):
            falta.append(f"{e['n']:02d}")
    return falta

def candidatos():
    cs = []
    for gj in sorted(glob.glob(os.path.join(BASE, 'contenido', '*', 'guion.json'))):
        c = os.path.dirname(gj)
        if SOLO and os.path.basename(c) != SOLO:
            continue
        if os.path.exists(os.path.join(c, 'subido.json')):
            continue
        cs.append(c)
    return cs

def subir(yt, archivo, portada, g, descripcion):
    from googleapiclient.http import MediaFileUpload
    pub = datetime.fromisoformat(g['publicar'].replace('Z', '+00:00')) if g.get('publicar') else None
    ahora = datetime.now(timezone.utc)
    status = {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': True,
              'embeddable': True, 'license': 'youtube'}
    programado = bool(pub and pub > ahora + timedelta(hours=1))
    if programado:
        status['publishAt'] = pub.strftime('%Y-%m-%dT%H:%M:%SZ')
    body = {'snippet': {'title': g['titulo'][:100], 'description': descripcion[:4900],
                        'tags': (g.get('tags') or []) + ['sw3', f"sw3_{g['id']}"],
                        'categoryId': str(g.get('categoria', '10')), 'defaultLanguage': g.get('idioma', 'hi'),
                        'defaultAudioLanguage': g.get('idioma', 'hi')},
            'status': status}
    try:
        r = yt.videos().insert(part='snippet,status', body=body,
                               media_body=MediaFileUpload(archivo, chunksize=-1, resumable=True)).execute()
    except Exception as e:
        if 'containsSyntheticMedia' not in str(e):
            raise
        body['status'].pop('containsSyntheticMedia', None)
        r = yt.videos().insert(part='snippet,status', body=body,
                               media_body=MediaFileUpload(archivo, chunksize=-1, resumable=True)).execute()
    vid = r['id']
    extras = []
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(portada, mimetype='image/jpeg')).execute()
        extras.append('portada OK')
    except Exception as e:
        extras.append(f'portada ERROR: {str(e)[:80]}')
    nombre = PLAYLISTS.get(g.get('formato'))
    if nombre:
        try:
            pls = yt.playlists().list(part='snippet', mine=True, maxResults=50).execute().get('items', [])
            pid = next((p['id'] for p in pls if p['snippet']['title'] == nombre), None)
            if not pid:
                pid = yt.playlists().insert(part='snippet,status', body={'snippet': {'title': nombre, 'defaultLanguage': 'hi'},
                                                                         'status': {'privacyStatus': 'public'}}).execute()['id']
            yt.playlistItems().insert(part='snippet', body={'snippet': {'playlistId': pid,
                                      'resourceId': {'kind': 'youtube#video', 'videoId': vid}}}).execute()
            extras.append('playlist OK')
        except Exception as e:
            extras.append(f'playlist ERROR: {str(e)[:80]}')
    return vid, programado, extras

def producir(carpeta):
    g = json.load(open(os.path.join(carpeta, 'guion.json'), encoding='utf-8'))
    falta = faltantes(carpeta, g)
    if falta and not PERMITIR_BANCO:
        avisar(f"⏸ <b>{g['id']}</b>: faltan imagenes {', '.join(falta)}. Ponlas en contenido/{g['id']}/imagenes/ y vuelve a subir.")
        return False
    tmp = os.path.join('/tmp', 'v3_' + g['id'])
    shutil.rmtree(tmp, ignore_errors=True)
    motores = set()
    def gen(texto, salida):
        motores.add(voz.generar(texto, salida))
    final, capitulos, total, img_portada, avisos = montaje.montar(carpeta, gen, tmp)
    m = g.get('miniatura', {})
    portada = os.path.join(tmp, 'portada.jpg')
    pv.portada(Image.open(img_portada), m.get('formato', g.get('formato', 'katha')), m.get('lineas', [g['titulo'][:20]]),
               m.get('gancho'), m.get('insignia'), m.get('paleta', 'fuego'), portada, fecha=m.get('fecha'))
    shutil.copy(portada, os.path.join(carpeta, 'portada.jpg'))
    desc = g['descripcion'].replace('{CAPITULOS}', capitulos or '')
    yt = youtube()
    vid, programado, extras = subir(yt, final, portada, g, desc)
    url = f"https://youtu.be/{vid}"
    json.dump({'video_id': vid, 'url': url, 'subido': datetime.now(timezone.utc).isoformat(timespec='seconds'),
               'publicar': g.get('publicar'), 'duracion_s': round(total), 'voz': sorted(motores)},
              open(os.path.join(carpeta, 'subido.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    cuando = g.get('publicar_texto') or g.get('publicar')
    avisar(f"🎬 <b>VIDEO NUEVO LISTO</b> (en privado)\n{g['titulo']}\n⏱ {montaje.mmss(total)} · voz: {', '.join(sorted(motores))}\n"
           + (f"📅 Se publica solo: {cuando}\n" if programado else "⚠️ La fecha ya paso: quedo en PRIVADO, publicalo a mano.\n")
           + f"🔗 {url}\n" + ' · '.join(extras) + ('\n' + '\n'.join(avisos) if avisos else '')
           + "\nRevisalo en Studio. Si esta bien no hagas nada.")
    return True

def main():
    cs = candidatos()
    if not cs:
        print("No hay videos pendientes."); return
    for c in cs:
        try:
            if producir(c):
                break           # uno por ejecucion por la cuota de YouTube
        except Exception as e:
            traceback.print_exc()
            avisar(f"❌ <b>{os.path.basename(c)}</b>: error en la produccion: {str(e)[:300]}")
            sys.exit(1)

if __name__ == '__main__':
    main()
