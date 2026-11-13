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

def banco_ganesha():
    imgs = sorted(glob.glob(os.path.join(BASE, 'assets', 'backgrounds', 'ganesha*.jpg')))
    return imgs

def imagen_escena(carpeta, n, semilla):
    for ext in ('png', 'jpg', 'jpeg', 'webp'):
        p = os.path.join(carpeta, 'imagenes', f'{n:02d}.{ext}')
        if os.path.exists(p):
            return p, False
    banco = banco_ganesha()
    if not banco:
        raise RuntimeError(f"Falta imagenes/{n:02d}.png y no hay banco de imagenes")
    random.seed(f"{semilla}-{n}")
    return random.choice(banco), True

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

def render_escena(i, img, audio, texto, capitulo, tmp, salida):
    d = dur(audio) + 0.8
    subs = trozos(texto)
    total_c = sum(len(s) for s in subs) or 1
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
    for i, e in enumerate(g['escenas']):
        n = e['n']; tipo = e.get('tipo', 'escena')
        img, de_banco = imagen_escena(carpeta, n, g['id'])
        if de_banco:
            avisos.append(f"escena {n:02d}: sin imagen propia, use una del banco")
        out = os.path.join(tmp, f'esc{n:02d}.mp4')
        audio = None
        if tipo != 'silencio' and e.get('texto'):
            audio = os.path.join(carpeta, 'voz', f'{n:02d}.mp3')
            generar_voz(e['texto'], audio)
        if tipo == 'escena':
            d = render_escena(i, img, audio, e['texto'], e['capitulo'], tmp, out)
        else:
            fondo = os.path.join(tmp, f'fondo{n:02d}.jpg'); fondo_borroso(img, fondo)
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
        "[1:a]volume=0.16[b];[0:a][b]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', final])
    # capitulos: YouTube pide el primero en 0:00, al menos 3 y de 10 s o mas
    limpio = []
    for s, c in caps:
        if limpio and s - limpio[-1][0] < 10:
            continue
        limpio.append((s, c))
    capitulos = '\n'.join(f"{mmss(s)} {c}" for s, c in limpio) if len(limpio) >= 3 else ''
    mini = g.get('miniatura', {}).get('imagen')
    img_portada = imagen_escena(carpeta, int(mini), g['id'])[0] if mini else imagen_escena(carpeta, 1, g['id'])[0]
    return final, capitulos, total, img_portada, avisos
