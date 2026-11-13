"""Portadas v3: 4 estilos (katha, mantra, chaturthi, aarti) x paletas, texto hindi grande y llamativo."""
import os, math, random, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageChops

F = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets', 'fonts')
def fuente(nombre, t):
    return ImageFont.truetype(os.path.join(F, nombre), t, layout_engine=ImageFont.Layout.RAQM)

PALETAS = {  # fondo1, fondo2, color_titulo, contorno, acento, texto_acento
 'fuego':   ((120, 10, 0), (255, 120, 0), (255, 230, 40), (40, 0, 0), (220, 20, 30), (255, 255, 255)),
 'real':    ((20, 10, 70), (120, 40, 170), (255, 210, 60), (20, 0, 40), (255, 170, 0), (30, 10, 0)),
 'noche':   ((5, 10, 40), (20, 60, 140), (255, 255, 255), (0, 0, 30), (230, 30, 60), (255, 255, 255)),
 'azafran': ((180, 60, 0), (255, 170, 20), (255, 255, 255), (110, 20, 0), (140, 0, 60), (255, 240, 200)),
 'jade':    ((0, 60, 50), (0, 150, 110), (255, 235, 90), (0, 30, 20), (230, 50, 30), (255, 255, 255)),
 'rosa':    ((110, 0, 60), (240, 60, 120), (255, 240, 120), (50, 0, 20), (255, 200, 0), (60, 0, 20)),
}

def degradado(w, h, c1, c2, radial=False):
    im = Image.new('RGB', (w, h), c1)
    px = im.load()
    for y in range(h):
        for x in range(0, w, 2):
            if radial:
                t = min(1, math.hypot((x - w * 0.7) / w, (y - h * 0.45) / h) * 1.6)
                t = 1 - t
            else:
                t = (x / w) * 0.6 + (y / h) * 0.4
            c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            px[x, y] = c
            if x + 1 < w:
                px[x + 1, y] = c
    return im

def rayos(w, h, centro, color, n=18, alfa=60):
    capa = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    cx, cy = centro
    for i in range(n):
        a1 = (i / n) * 2 * math.pi
        a2 = a1 + math.pi / n
        R = max(w, h) * 1.5
        d.polygon([(cx, cy), (cx + R * math.cos(a1), cy + R * math.sin(a1)), (cx + R * math.cos(a2), cy + R * math.sin(a2))],
                  fill=color + (alfa,))
    return capa.filter(ImageFilter.GaussianBlur(6))

def texto_contorno(d, xy, txt, f, relleno, contorno, grosor, anchor='la'):
    d.text(xy, txt, font=f, fill=relleno, stroke_width=grosor, stroke_fill=contorno, anchor=anchor)

def ajustar(txt, nombre, max_w, t0, t_min=40):
    t = t0
    while t > t_min:
        f = fuente(nombre, t)
        if f.getbbox(txt)[2] <= max_w:
            return f
        t -= 4
    return fuente(nombre, t_min)

def sombra_texto(base, xy, txt, f, rad=14, alfa=200, off=(8, 10), anchor='la'):
    capa = Image.new('RGBA', base.size, (0, 0, 0, 0))
    ImageDraw.Draw(capa).text((xy[0] + off[0], xy[1] + off[1]), txt, font=f, fill=(0, 0, 0, alfa), anchor=anchor,
                              stroke_width=10, stroke_fill=(0, 0, 0, alfa))
    base.alpha_composite(capa.filter(ImageFilter.GaussianBlur(rad)))

def sujeto(img, w, h, lado='der', ancho=0.62, tinte=None, fuerza=0.0):
    """Coloca la imagen del sujeto ocupando el lado indicado, con borde suave y brillo."""
    s = ImageOps.fit(img.convert('RGB'), (int(w * ancho), h), Image.LANCZOS, centering=(0.5, 0.35))
    s = ImageEnhance.Color(s).enhance(1.35)
    s = ImageEnhance.Contrast(s).enhance(1.15)
    if tinte:
        s = Image.blend(s, Image.new('RGB', s.size, tinte), fuerza)
    m = Image.new('L', s.size, 255)
    dm = ImageDraw.Draw(m)
    borde = int(s.size[0] * 0.35)
    for i in range(borde):
        v = int(255 * (i / borde) ** 1.4)
        x = i if lado == 'der' else s.size[0] - 1 - i
        dm.line([(x, 0), (x, h)], fill=v)
    return s, m

def pastilla(base, xy, txt, f, bg, fg, pad=(26, 12), radio=18, anchor_der=False):
    d = ImageDraw.Draw(base)
    bb = d.textbbox((0, 0), txt, font=f)
    wt, ht = bb[2] - bb[0], bb[3] - bb[1]
    x, y = xy
    if anchor_der:
        x = x - wt - 2 * pad[0]
    d.rounded_rectangle([x, y, x + wt + 2 * pad[0], y + ht + 2 * pad[1] + 8], radius=radio, fill=bg)
    d.text((x + pad[0] - bb[0], y + pad[1] - bb[1] + 4), txt, font=f, fill=fg)
    return x + wt + 2 * pad[0], y + ht + 2 * pad[1] + 8

def portada(img, formato, lineas, gancho, insignia, paleta, salida, fecha=None, W=1280, H=720):
    c1, c2, ct, co, ca, cta = PALETAS[paleta]
    base = degradado(W, H, c1, c2, radial=formato in ('mantra', 'chaturthi')).convert('RGBA')
    if formato in ('katha', 'aarti'):
        base.alpha_composite(rayos(W, H, (int(W * 0.72), int(H * 0.42)), (255, 255, 200), alfa=45))
    # sujeto
    ancho = 0.60 if formato != 'mantra' else 0.55
    fz = {'noche': 0.38, 'real': 0.22, 'jade': 0.25, 'rosa': 0.22}.get(paleta, 0.0)
    s, m = sujeto(img, W, H, 'der', ancho, c2, fz)
    if formato == 'mantra':  # sujeto en circulo con aro dorado
        dia = int(H * 0.80)
        sc = ImageOps.fit(img.convert('RGB'), (dia, dia), Image.LANCZOS, centering=(0.5, 0.3))
        sc = ImageEnhance.Color(sc).enhance(1.3)
        if fz:
            sc = Image.blend(sc, Image.new('RGB', sc.size, c2), fz)
        mc = Image.new('L', (dia, dia), 0); ImageDraw.Draw(mc).ellipse([0, 0, dia, dia], fill=255)
        cx, cy = int(W * 0.755), int(H * 0.5)
        aro = Image.new('RGBA', (W, H), (0, 0, 0, 0)); da = ImageDraw.Draw(aro)
        da.ellipse([cx - dia // 2 - 18, cy - dia // 2 - 18, cx + dia // 2 + 18, cy + dia // 2 + 18], fill=ca + (255,))
        base.alpha_composite(aro.filter(ImageFilter.GaussianBlur(30)))
        base.alpha_composite(aro)
        base.paste(sc, (cx - dia // 2, cy - dia // 2), mc)
    else:
        sombra = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        base.paste(s, (W - s.size[0], 0), m)
    if formato == 'chaturthi':  # luna
        luna = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(luna)
        dl.ellipse([W - 330, 50, W - 130, 250], fill=(255, 248, 215, 255))
        corte = Image.new('L', (W, H), 0)
        ImageDraw.Draw(corte).ellipse([W - 280, 25, W - 80, 225], fill=255)
        luna.putalpha(ImageChops.subtract(luna.getchannel('A'), corte))
        glow = luna.filter(ImageFilter.GaussianBlur(28))
        base.alpha_composite(glow); base.alpha_composite(glow); base.alpha_composite(luna)
        random.seed(paleta)
        de = ImageDraw.Draw(base)
        for _ in range(90):
            x, y = random.randint(0, W), random.randint(0, H)
            r = random.choice([1, 1, 2])
            de.ellipse([x, y, x + r, y + r], fill=(255, 255, 255, random.randint(120, 255)))
    # oscurecer zona del texto
    grad = Image.new('L', (W, H), 0); dg = ImageDraw.Draw(grad)
    for x in range(int(W * 0.62)):
        dg.line([(x, 0), (x, H)], fill=int(170 * (1 - x / (W * 0.62)) ** 1.2))
    base.alpha_composite(Image.composite(Image.new('RGBA', (W, H), (0, 0, 0, 255)), Image.new('RGBA', (W, H), (0, 0, 0, 0)), grad))
    d = ImageDraw.Draw(base)
    # titulo (1-2 lineas) muy grande
    nombre_f = {'katha': 'baloo8.ttf', 'mantra': 'yatra.ttf', 'chaturthi': 'baloo8.ttf', 'aarti': 'khand7.ttf'}[formato]
    max_w = int(W * (0.50 if formato == 'mantra' else 0.60))
    y = 70 if formato != 'chaturthi' else 150
    tam = 150 if len(lineas) == 1 else 128
    for i, ln in enumerate(lineas):
        f = ajustar(ln, nombre_f, max_w, tam + (10 if formato == 'aarti' else 0))
        sombra_texto(base, (52, y), ln, f)
        d = ImageDraw.Draw(base)
        color = ct if i == 0 else (255, 255, 255)
        texto_contorno(d, (52, y), ln, f, color, co, 10)
        bb = d.textbbox((52, y), ln, font=f)
        y = bb[3] + 18
    # gancho en banda de color
    if gancho:
        fg = ajustar(gancho, 'baloo8.ttf', int(W * 0.56), 64, 36)
        bb = d.textbbox((0, 0), gancho, font=fg)
        yb = max(y + 10, H - 175)
        d.rectangle([0, yb, 52 + bb[2] + 40, yb + (bb[3] - bb[1]) + 36], fill=ca)
        d.text((52, yb + 18 - bb[1]), gancho, font=fg, fill=cta)
    # insignia
    if insignia:
        fi = fuente('baloo8.ttf' if any('ऀ' <= ch <= 'ॿ' for ch in insignia) else 'teko7_latin.ttf', 54)
        pastilla(base, (W - 40, 34), insignia, fi, (230, 20, 30), (255, 255, 255), anchor_der=True)
    if fecha:
        ff = fuente('baloo8.ttf', 70)
        pastilla(base, (52, 40), fecha, ff, (255, 255, 255), (200, 0, 30), pad=(24, 6))
    # marca
    fm = fuente('teko7_latin.ttf', 30)
    d = ImageDraw.Draw(base)
    d.text((W - 24, H - 20), 'SpiritualWave', font=fm, fill=(255, 255, 255, 190), anchor='rs')
    base.convert('RGB').save(salida, quality=92)
    return salida
