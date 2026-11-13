"""Montaje v3: arma el video completo desde guion.json + voz + imagenes.
Tipos de escena: 'escena' (imagen + voz + subtitulos), 'tarjeta' (datos en pantalla), 'letra' (texto sagrado
con transliteracion y significado), 'japa' (mantra N veces con contador), 'silencio' (meditacion sin voz)."""
import os, re, json, glob, random, shutil, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import portadas_v3 as pv

W, H, FPS = 1920, 1080, 25
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUENTE_NUM = os.path.join(BASE, 'assets', 'fonts', 'baloo8.ttf')

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {' '.join(cmd[:6])}...\n{r.stderr[-1500:]}")
    return r

def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

EXT_IMG = ('png', 'jpg', 'jpeg', 'webp')
EXT_VID = ('mp4', 'mov', 'webm', 'm4v')

def banco_ganesha():
    return sorted(glob.glob(os.path.join(BASE, 'assets', 'backgrounds', 'ganesha*.jpg')))

def banco_clips():
    c = []
    for ext in ('mp4', 'mov', 'webm', 'm4v'):
        c += glob.glob(os.path.join(BASE, 'assets', 'videos_ganesha_horizontal', f'*.{ext}'))
    return sorted(c)

_ORDEN = {}
def clip_del_banco(semilla, n):
    """Un clip distinto por escena dentro del mismo video (orden barajado fijo por video)."""
    clips = banco_clips()
    if not clips:
        return None
    if semilla not in _ORDEN:
        o = list(clips); random.Random(semilla).shuffle(o); _ORDEN[semilla] = o
    o = _ORDEN[semilla]
    return o[(n - 1) % len(o)]

def media_escena(carpeta, n, semilla):
    """Devuelve (ruta, es_video, de_banco). Prioridad: video propio > imagen propia > clip del banco > imagen del banco."""
    for ext in EXT_VID:
        p = os.path.join(carpeta, 'imagenes', f'{n:02d}.{ext}')
        if os.path.exists(p):
            return p, True, False
    for ext in EXT_IMG:
        p = os.path.join(carpeta, 'imagenes', f'{n:02d}.{ext}')
        if os.path.exists(p):
            return p, False, False
    clip = clip_del_banco(semilla, n)
    if clip:
        return clip, True, True
    random.seed(f"{semilla}-{n}")
    banco = banco_ganesha()
    if not banco:
        raise RuntimeError(f"Falta imagenes/{n:02d} y no hay banco de imagenes ni clips")
    return random.choice(banco), False, True

def imagen_escena(carpeta, n, semilla):
    """Compatibilidad: siempre una imagen fija (para fondos y portadas)."""
    p, es_video, banco = media_escena(carpeta, n, semilla)
    return p, banco

def fotograma(video, salida, t=1.0):
    sh(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i', video, '-frames:v', '1', '-q:v', '2', salida])
    return salida

def fija(media, es_video, tmp, nombre):
    return fotograma(media, os.path.join(tmp, nombre)) if es_video else media

def preparar_clip(video, tmp, i):
    """Clip corto -> bucle suave ida y vuelta (sin saltos), 1920x1080, 25 fps, sin audio, un poco mas lento."""
    ida = os.path.join(tmp, f'clip{i}_ida.mp4'); vuelta = os.path.join(tmp, f'clip{i}_vuelta.mp4')
    bucle = os.path.join(tmp, f'clip{i}_bucle.mp4')
    sh(['ffmpeg', '-y', '-v', 'error', '-i', video, '-t', '8', '-an', '-vf',
        f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setpts=1.25*PTS,eq=saturation=1.12',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', ida])
    sh(['ffmpeg', '-y', '-v', 'error', '-i', ida, '-vf', 'reverse', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
        '-pix_fmt', 'yuv420p', vuelta])
    lst = os.path.join(tmp, f'clip{i}.txt')
    open(lst, 'w').write(f"file '{ida}'\nfile '{vuelta}'\n")
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', bucle])
    return bucle

# ---------- piezas graficas (PNG transparentes) ----------
def png_subtitulo(texto, salida):
    f = pv.fuente('hind7.ttf', 64)
    lineas = []
    for parte in textwrap.wrap(texto, 44):
        lineas.append(parte)
    lineas = lineas[:2]
    im = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 30 if len(lineas) == 2 else 90
    for ln in lineas:
        d.text((W // 2, y + 40), ln, font=f, fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=(0, 0, 0))
        y += 92
    im.save(salida)

def png_chip(texto, salida, bg=(220, 20, 30), fg=(255, 255, 255)):
    im = Image.new('RGBA', (W, 160), (0, 0, 0, 0))
    pv.pastilla(im, (60, 40), texto, pv.fuente('baloo8.ttf', 44), bg, fg)
    im.save(salida)

def png_marca(salida):
    im = Image.new('RGBA', (W, 120), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((W - 40, 40), 'SpiritualWave', font=pv.fuente('teko7_latin.ttf', 42), fill=(255, 255, 255, 190), anchor='ra')
    im.save(salida)

def fondo_borroso(img_path, salida, tinte=(10, 10, 40), fuerza=0.55):
    b = ImageOps.fit(Image.open(img_path).convert('RGB'), (W, H), Image.LANCZOS, centering=(0.5, 0.35))
    b = Image.blend(ImageEnhance.Color(b).enhance(1.2), Image.new('RGB', (W, H), tinte), fuerza).filter(ImageFilter.GaussianBlur(20))
    b.save(salida, quality=92)

def png_tarjeta(titulo, filas, salida, pie=None):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([140, 140, W - 140, H - 120], radius=40, fill=(10, 12, 40, 215), outline=(255, 200, 60), width=4)
    d.text((W // 2, 240), titulo, font=pv.ajustar(titulo, 'baloo8.ttf', W - 400, 92), fill=(255, 215, 80), anchor='mm')
    y = 390
    paso = min(125, int(560 / max(1, len(filas))))
    for k, v in filas:
        d.text((250, y), k, font=pv.fuente('baloo8.ttf', 58), fill=(255, 170, 60), anchor='lm')
        d.text((640, y), v, font=pv.ajustar(v, 'hind7.ttf', W - 640 - 200, 56, 34), fill=(255, 255, 255), anchor='lm')
        y += paso
    if pie:
        d.text((W // 2, H - 175), pie, font=pv.fuente('hind7.ttf', 38), fill=(200, 200, 225), anchor='mm')
    im.save(salida)

def png_letra(deva, translit, significado, salida):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([160, 230, W - 160, H - 150], radius=36, fill=(25, 8, 0, 200), outline=(255, 190, 60), width=4)
    y = 330
    for ln in deva.split('\n'):
        f = pv.ajustar(ln, 'baloo8.ttf', W - 420, 86, 50)
        d.text((W // 2, y), ln, font=f, fill=(255, 215, 90), anchor='mm', stroke_width=3, stroke_fill=(60, 20, 0))
        y += 105
    y += 10
    for ln in textwrap.wrap(translit, 60):
        d.text((W // 2, y), ln, font=pv.fuente('baloo8.ttf', 46), fill=(255, 255, 255), anchor='mm')
        y += 62
    y += 14
    for ln in textwrap.wrap(significado, 58)[:3]:
        d.text((W // 2, y), ln, font=pv.fuente('hind7.ttf', 44), fill=(255, 225, 190), anchor='mm')
        y += 58
    im.save(salida)

def png_japa(mantra, translit, salida):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, R = W // 2, 470, 300
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 200, 40, 230), width=20)
    d.text((cx, cy + 125), '/ 108', font=pv.fuente('baloo8.ttf', 68), fill=(255, 210, 120), anchor='mm')
    d.text((cx, 865), mantra, font=pv.ajustar(mantra, 'yatra.ttf', W - 200, 118, 60), fill=(255, 215, 80), anchor='mm', stroke_width=6, stroke_fill=(40, 10, 0))
    d.text((cx, 978), translit, font=pv.ajustar(translit, 'baloo8.ttf', W - 300, 54, 30), fill=(255, 255, 255), anchor='mm')
    pv.pastilla(im, (60, 50), 'जाप · 108', pv.fuente('baloo8.ttf', 46), (255, 170, 0), (40, 10, 0))
    im.save(salida)

def trozos(texto):
    """Divide el texto en frases cortas para los subtitulos."""
    partes = re.split(r'(?<=[।?!,])\s+', texto.strip())
    salida, actual = [], ''
    for p in partes:
        if len(actual) + len(p) + 1 <= 80:
            actual = (actual + ' ' + p).strip()
        else:
            if actual:
                salida.append(actual)
            actual = p
    if actual:
        salida.append(actual)
    return salida

# ---------- render de cada tipo de escena ----------
ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', str(FPS),
       '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2']

def kenburns(i):
    if i % 2 == 0:
        return "zoompan=z='min(1+0.00045*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=25"
    return "zoompan=z='max(1.12-0.00045*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':d=1:s=1920x1080:fps=25"

def render_escena(i, img, audio, texto, capitulo, tmp, salida, es_video=False):
    d = dur(audio) + 0.8
    subs = trozos(texto)
    total_c = sum(len(s) for s in subs) or 1
    if es_video:
        entradas = ['-stream_loop', '-1', '-i', preparar_clip(img, tmp, i), '-i', audio]
    else:
        entradas = ['-loop', '1', '-framerate', str(FPS), '-t', f'{d:.2f}', '-i', img, '-i', audio]
    capas = []
    png_chip(capitulo, os.path.join(tmp, f'chip{i}.png'))
    capas.append((os.path.join(tmp, f'chip{i}.png'), 0, 0.4, 4.5))
    t = 0.15
    util = d - 0.95
    for k, s in enumerate(subs):
        p = os.path.join(tmp, f'sub{i}_{k}.png'); png_subtitulo(s, p)
        dt = util * len(s) / total_c
        capas.append((p, H - 300, t, t + dt))
        t += dt
    if es_video:
        fil = [f"[0:v]setpts=PTS-STARTPTS,format=rgba[v0]"]
    else:
        fil = [f"[0:v]scale=2304:1296:force_original_aspect_ratio=increase,crop=2304:1296,{kenburns(i)},"
               f"eq=saturation=1.15,format=rgba[v0]"]
    # degradado inferior para leer los subtitulos
    grad = os.path.join(tmp, 'grad.png')
    if not os.path.exists(grad):
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
        for y in range(620, H):
            dg.line([(0, y), (W, y)], fill=(0, 0, 0, int(225 * ((y - 620) / (H - 620)) ** 0.8)))
        g.save(grad)
        png_marca(os.path.join(tmp, 'marca.png'))
    entradas += ['-i', grad, '-i', os.path.join(tmp, 'marca.png')]
    fil.append("[v0][2:v]overlay=0:0[v1]")
    fil.append("[v1][3:v]overlay=0:20[v2]")
    ult = 'v2'
    for k, (p, y, a, b) in enumerate(capas):
        entradas += ['-i', p]
        idx = 4 + k
        fil.append(f"[{ult}][{idx}:v]overlay=0:{y}:enable='between(t,{a:.2f},{b:.2f})'[c{k}]")
        ult = f'c{k}'
    fil.append(f"[{ult}]fade=t=in:st=0:d=0.4,fade=t=out:st={d - 0.45:.2f}:d=0.45,format=yuv420p[vout]")
    fil.append(f"[1:a]apad=pad_dur=1,atrim=0:{d:.2f},afade=t=in:d=0.05[aout]")
    sh(['ffmpeg', '-y', '-v', 'error', *entradas, '-filter_complex', ';'.join(fil), '-map', '[vout]', '-map', '[aout]',
        '-t', f'{d:.2f}', *ENC, salida])
    return d

def render_estatica(fondo, capa_png, audio, d, salida):
    entradas = ['-loop', '1', '-framerate', str(FPS), '-t', f'{d:.2f}', '-i', fondo, '-loop', '1', '-framerate', str(FPS),
                '-t', f'{d:.2f}', '-i', capa_png]
    if audio:
        entradas += ['-i', audio]
        amap = f"[2:a]apad=pad_dur=1,atrim=0:{d:.2f}[aout]"
    else:
        entradas += ['-f', 'lavfi', '-t', f'{d:.2f}', '-i', 'anullsrc=r=48000:cl=stereo']
        amap = "[2:a]anull[aout]"
    fil = [f"[0:v]scale={W}:{H},format=rgba[b];[b][1:v]overlay=0:0,fade=t=in:st=0:d=0.4,fade=t=out:st={d - 0.45:.2f}:d=0.45,format=yuv420p[vout]", amap]
    sh(['ffmpeg', '-y', '-v', 'error', *entradas, '-filter_complex', ';'.join(fil), '-map', '[vout]', '-map', '[aout]',
        '-t', f'{d:.2f}', *ENC, salida])
    return d

def render_japa(fondo, capa_png, rep_audio, n, tmp, salida):
    rep = os.path.join(tmp, 'rep.wav')
    sh(['ffmpeg', '-y', '-v', 'error', '-i', rep_audio, '-af', 'apad=pad_dur=0.9', '-ar', '48000', '-ac', '2', rep])
    R = dur(rep)
    d = R * n + 1.0
    filtro = os.path.join(tmp, 'japa.txt')
    num = FUENTE_NUM.replace('\\', '/').replace(':', '\\\\:')
    with open(filtro, 'w', encoding='utf-8') as f:
        f.write(f"[0:v]scale={W}:{H},format=rgba[b];[b][1:v]overlay=0:0,"
                f"drawtext=fontfile='{num}':text='%{{eif\\:min({n}\\,floor(t/{R:.4f})+1)\\:d}}':"
                f"fontsize=230:fontcolor=white:x=(w-text_w)/2:y=470-text_h/2-40,"
                f"fade=t=in:st=0:d=0.5,format=yuv420p[vout];"
                f"[2:a]atrim=0:{d:.2f}[aout]")
    sh(['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-framerate', str(FPS), '-t', f'{d:.2f}', '-i', fondo,
        '-loop', '1', '-framerate', str(FPS), '-t', f'{d:.2f}', '-i', capa_png,
        '-stream_loop', str(n), '-i', rep, '-filter_complex_script', filtro, '-map', '[vout]', '-map', '[aout]',
        '-t', f'{d:.2f}', *ENC, salida])
    return d

# ---------- formato "mantra cantado": cancion (Suno) + clips + letra en pantalla ----------
EXT_AUD = ('mp3', 'wav', 'm4a', 'flac', 'ogg')

def canciones(carpeta):
    c = []
    for ext in EXT_AUD:
        c += glob.glob(os.path.join(carpeta, 'musica', f'*.{ext}'))
    return sorted(c)

def png_estrofa(deva, translit, significado, salida):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lineas = [l for l in deva.split('\n') if l.strip()]
    alto = 70 + 92 * len(lineas) + (58 if translit else 0) * max(1, len(textwrap.wrap(translit, 64))) + 56 * len(textwrap.wrap(significado, 62)[:2]) + 40
    y0 = H - 40 - alto
    d.rounded_rectangle([110, y0, W - 110, H - 40], radius=34, fill=(15, 5, 0, 190), outline=(255, 190, 60, 230), width=3)
    y = y0 + 70
    for ln in lineas:
        f = pv.ajustar(ln, 'baloo8.ttf', W - 340, 76, 44)
        d.text((W // 2, y), ln, font=f, fill=(255, 215, 90), anchor='mm', stroke_width=3, stroke_fill=(60, 20, 0))
        y += 92
    for ln in textwrap.wrap(translit, 64):
        d.text((W // 2, y), ln, font=pv.fuente('baloo8.ttf', 42), fill=(255, 255, 255), anchor='mm')
        y += 58
    for ln in textwrap.wrap(significado, 62)[:2]:
        d.text((W // 2, y), ln, font=pv.fuente('hind7.ttf', 40), fill=(255, 225, 190), anchor='mm')
        y += 56
    im.save(salida)

_CLIPS_LISTOS = {}
def clip_10s(video, tmp):
    if video in _CLIPS_LISTOS:
        return _CLIPS_LISTOS[video]
    out = os.path.join(tmp, f'c10_{len(_CLIPS_LISTOS):03d}.mp4')
    sh(['ffmpeg', '-y', '-v', 'error', '-stream_loop', '-1', '-i', video, '-t', '10', '-an', '-vf',
        f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=saturation=1.12,'
        f'fade=t=in:st=0:d=0.5,fade=t=out:st=9.5:d=0.5',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out])
    _CLIPS_LISTOS[video] = out
    return out

def render_cancion(carpeta, e, semilla, tmp, salida):
    songs = canciones(carpeta)
    if not songs:
        raise RuntimeError("falta la cancion en la carpeta musica/")
    T = float(e.get('minutos', 12)) * 60
    # audio: las versiones de la cancion alternadas hasta cubrir T, con 1.5 s de respiro entre vueltas
    wavs = []
    for k, sg in enumerate(songs):
        wv = os.path.join(tmp, f'song{k}.wav')
        sh(['ffmpeg', '-y', '-v', 'error', '-i', sg, '-af', 'apad=pad_dur=1.5', '-ar', '48000', '-ac', '2', wv])
        wavs.append(wv)
    lst, acum, k = [], 0.0, 0
    while acum < T:
        lst.append(wavs[k % len(wavs)]); acum += dur(wavs[k % len(wavs)]); k += 1
    la = os.path.join(tmp, 'songs.txt'); open(la, 'w').write(''.join(f"file '{w}'\n" for w in lst))
    audio = os.path.join(tmp, 'cancion_larga.wav')
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', la, '-t', f'{T:.2f}',
        '-af', f'afade=t=out:st={T - 6:.2f}:d=6', '-ar', '48000', '-ac', '2', audio])
    # video: clips del canal, uno distinto cada 10 s, en orden barajado fijo por video
    clips = banco_clips()
    if not clips:
        raise RuntimeError("no hay clips en assets/videos_ganesha_horizontal")
    orden = list(clips); random.Random(semilla + '-cancion').shuffle(orden)
    n = int(T // 10) + 1
    lv = os.path.join(tmp, 'clips.txt')
    open(lv, 'w').write(''.join(f"file '{clip_10s(orden[j % len(orden)], tmp)}'\n" for j in range(n)))
    fondo = os.path.join(tmp, 'fondo_cancion.mp4')
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lv, '-t', f'{T:.2f}', '-c', 'copy', fondo])
    # estrofas rotando cada N segundos
    letras = e.get('letras', [])
    seg = float(e.get('seg_estrofa', 18))
    entradas = ['-i', fondo, '-i', audio]
    if not os.path.exists(os.path.join(tmp, 'marca.png')):
        png_marca(os.path.join(tmp, 'marca.png'))
    entradas += ['-i', os.path.join(tmp, 'marca.png')]
    fil = ["[0:v]format=rgba[v0]", "[v0][2:v]overlay=0:20[v1]"]
    ult = 'v1'
    ciclo = seg * max(1, len(letras))
    for k, L in enumerate(letras):
        p = os.path.join(tmp, f'estrofa{k}.png')
        png_estrofa(L['deva'], L.get('translit', ''), L.get('sig', ''), p)
        entradas += ['-i', p]
        a, b = k * seg, (k + 1) * seg
        fil.append(f"[{ult}][{3 + k}:v]overlay=0:0:enable='between(mod(t,{ciclo:.2f}),{a + 0.3:.2f},{b - 0.3:.2f})'[l{k}]")
        ult = f'l{k}'
    fil.append(f"[{ult}]fade=t=in:st=0:d=0.6,fade=t=out:st={T - 1.5:.2f}:d=1.5,format=yuv420p[vout]")
    sh(['ffmpeg', '-y', '-v', 'error', *entradas, '-filter_complex', ';'.join(fil), '-map', '[vout]', '-map', '1:a',
        '-t', f'{T:.2f}', *ENC, salida])
    return T

def tanpura(d, salida):
    """Fondo musical original: drone tipo tanpura (Sa-Pa-Sa), suave y sin voz."""
    propia = sorted(glob.glob(os.path.join(BASE, 'assets', 'music_fondo', '*.mp3')))
    if propia:
        sh(['ffmpeg', '-y', '-v', 'error', '-stream_loop', '-1', '-i', random.choice(propia), '-t', f'{d:.2f}',
            '-af', f'afade=t=in:d=3,afade=t=out:st={max(0, d - 5):.2f}:d=5', '-ar', '48000', '-ac', '2', salida])
        return
    D = f'{d:.2f}'
    fc = ("[0:a]volume=0.55,tremolo=f=0.13:d=0.35[a];[1:a]volume=0.30,tremolo=f=0.11:d=0.45[b];"
          "[2:a]volume=0.22,tremolo=f=0.17:d=0.5[c];[3:a]volume=0.10,tremolo=f=0.10:d=0.6[e];[4:a]lowpass=f=500,volume=0.6[n];"
          f"[a][b][c][e][n]amix=inputs=5:normalize=0,lowpass=f=1600,aecho=0.8:0.6:180|360:0.25|0.15,"
          f"afade=t=in:d=4,afade=t=out:st={max(0, d - 6):.2f}:d=6,volume=0.9")
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', f'sine=f=130.81:d={D}', '-f', 'lavfi', '-i', f'sine=f=196.0:d={D}',
        '-f', 'lavfi', '-i', f'sine=f=261.63:d={D}', '-f', 'lavfi', '-i', f'sine=f=392.0:d={D}',
        '-f', 'lavfi', '-i', f'anoisesrc=c=pink:a=0.015:d={D}', '-filter_complex', fc, '-ar', '48000', '-ac', '2', salida])

def mmss(s):
    s = int(round(s))
    h, r = divmod(s, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def montar(carpeta, generar_voz, tmp):
    """Devuelve (video_final, capitulos_texto, duracion, imagen_para_portada, avisos)."""
    g = json.load(open(os.path.join(carpeta, 'guion.json'), encoding='utf-8'))
    os.makedirs(tmp, exist_ok=True)
    partes, caps, t, avisos = [], [], 0.0, []
    sin_fondo = []   # tramos con cancion: ahi no va la tanpura
    for i, e in enumerate(g['escenas']):
        n = e['n']; tipo = e.get('tipo', 'escena')
        img, es_video, de_banco = media_escena(carpeta, n, g['id'])
        if de_banco:
            avisos.append(f"escena {n:02d}: sin imagen/video propio, use {'un clip' if es_video else 'una imagen'} del banco")
        out = os.path.join(tmp, f'esc{n:02d}.mp4')
        audio = None
        if tipo not in ('silencio', 'cancion') and e.get('texto'):
            audio = os.path.join(carpeta, 'voz', f'{n:02d}.mp3')
            generar_voz(e['texto'], audio)
        if tipo == 'escena':
            d = render_escena(i, img, audio, e['texto'], e['capitulo'], tmp, out, es_video)
        else:
            fondo = os.path.join(tmp, f'fondo{n:02d}.jpg'); fondo_borroso(fija(img, es_video, tmp, f'fija{n:02d}.jpg'), fondo)
            capa = os.path.join(tmp, f'capa{n:02d}.png')
            if tipo == 'tarjeta':
                png_tarjeta(e.get('titulo_tarjeta', e['capitulo']), e['filas'], capa, e.get('pie'))
                d = render_estatica(fondo, capa, audio, dur(audio) + 0.8, out)
            elif tipo == 'letra':
                png_letra(e['deva'], e.get('translit', ''), e.get('significado', ''), capa)
                d = render_estatica(fondo, capa, audio, dur(audio) + 0.8, out)
            elif tipo == 'japa':
                png_japa(e['mantra'], e.get('translit', ''), capa)
                rep = os.path.join(carpeta, 'voz', 'mantra.mp3')
                generar_voz(e['mantra'], rep)
                if audio:   # breve introduccion antes del japa
                    intro = os.path.join(tmp, f'esc{n:02d}a.mp4')
                    partes.append(intro)
                    di = render_estatica(fondo, capa, audio, dur(audio) + 0.8, intro)
                    caps.append((t, e['capitulo'])); t += di
                d = render_japa(fondo, capa, rep, int(e.get('repeticiones', 108)), tmp, out)
                partes.append(out)
                caps.append((t, e.get('capitulo_japa', 'मंत्र जाप 108')))
                t += d
                continue
            elif tipo == 'cancion':
                d = render_cancion(carpeta, e, g['id'], tmp, out)
                sin_fondo.append((t, t + d))
            elif tipo == 'silencio':
                png_tarjeta(e['capitulo'], e.get('filas', []), capa, e.get('pie'))
                d = render_estatica(fondo, capa, None, float(e.get('segundos', 60)), out)
            else:
                raise RuntimeError(f"tipo de escena desconocido: {tipo}")
        if not caps or caps[-1][1] != e['capitulo']:
            caps.append((t, e['capitulo']))
        partes.append(out)
        t += d
    lista = os.path.join(tmp, 'lista.txt')
    with open(lista, 'w') as f:
        for p in partes:
            f.write(f"file '{p}'\n")
    unido = os.path.join(tmp, 'unido.mp4')
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', unido])
    total = dur(unido)
    bed = os.path.join(tmp, 'fondo.wav'); tanpura(total, bed)
    final = os.path.join(tmp, f"{g['id']}.mp4")
    sh(['ffmpeg', '-y', '-v', 'error', '-i', unido, '-i', bed, '-filter_complex',
        "[1:a]volume=0.16" + ''.join(f",volume=0:enable='between(t,{a:.2f},{b:.2f})'" for a, b in sin_fondo)
        + "[b];[0:a][b]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', final])
    # capitulos: YouTube pide el primero en 0:00, al menos 3 y de 10 s o mas
    limpio = []
    for s, c in caps:
        if limpio and s - limpio[-1][0] < 10:
            continue
        limpio.append((s, c))
    capitulos = '\n'.join(f"{mmss(s)} {c}" for s, c in limpio) if len(limpio) >= 3 else ''
    mini = g.get('miniatura', {}).get('imagen')
    pm, pv_es, _ = media_escena(carpeta, int(mini) if mini else 1, g['id'])
    img_portada = fija(pm, pv_es, tmp, 'portada_base.jpg')
    return final, capitulos, total, img_portada, avisos
