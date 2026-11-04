# -*- coding: utf-8 -*-
"""Portadas llamativas (largo, short, live) y tarjetas de letra en devanagari.
Requiere Pillow con libraqm (en GitHub: apt install libraqm0 libfribidi0) y las fuentes de assets/fonts.
Si algo falta, disponible() devuelve False y el pipeline usa el diseno anterior (nunca se rompe)."""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(BASE, 'assets', 'fonts')
NECESARIAS = ('rozha_deva.ttf', 'teko7_latin.ttf', 'hind7_deva.ttf', 'hind7_latin.ttf')


def disponible():
    try:
        from PIL import features
        if not features.check('raqm'):
            return False
        return all(os.path.exists(os.path.join(FUENTES, f)) for f in NECESARIAS)
    except Exception:
        return False


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), int(tam), layout_engine=ImageFont.Layout.RAQM)


def _cubrir(img, w, h, foco=(0.5, 0.4)):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = int((img.width - w) * foco[0]); y = int((img.height - h) * foco[1])
    return img.crop((x, y, x + w, y + h))


def _degradado_oro(size, top=(255, 244, 170), bot=(255, 150, 20)):
    g = Image.new('RGB', size); d = ImageDraw.Draw(g)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        d.line([(0, y), (size[0], y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return g


def _texto(texto, font, relleno='oro', borde=10, brillo=True, pad=40):
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    bb = tmp.textbbox((0, 0), texto, font=font, stroke_width=borde)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    masc = Image.new('L', (w, h), 0); ImageDraw.Draw(masc).text((pad - bb[0], pad - bb[1]), texto, font=font, fill=255)
    cont = Image.new('L', (w, h), 0)
    ImageDraw.Draw(cont).text((pad - bb[0], pad - bb[1]), texto, font=font, fill=255, stroke_width=borde)
    capa = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if brillo:
        g = cont.filter(ImageFilter.GaussianBlur(14))
        capa.paste(Image.new('RGBA', (w, h), (255, 120, 0, 255)), (0, 0), g.point(lambda v: min(255, v * 2)))
    capa.paste(Image.new('RGBA', (w, h), (30, 5, 0, 255)), (0, 0), cont)
    col = _degradado_oro((w, h)) if relleno == 'oro' else Image.new('RGB', (w, h), (255, 255, 255))
    capa.paste(col, (0, 0), masc)
    return capa


def _rayos(size, centro, n=18, color=(255, 190, 60), alpha=70):
    L = Image.new('RGBA', size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    R = max(size) * 1.5
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = a0 + math.pi / n
        d.polygon([centro, (centro[0] + R * math.cos(a0), centro[1] + R * math.sin(a0)),
                   (centro[0] + R * math.cos(a1), centro[1] + R * math.sin(a1))], fill=color + (alpha,))
    return L.filter(ImageFilter.GaussianBlur(6))


def _fondo(bg, W, H, ancho_sujeto, foco=(0.5, 0.35), lado='derecha'):
    base = _cubrir(Image.open(bg).convert('RGB'), W, H, foco=(0.5, 0.4))
    base = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(base).enhance(1.35)).enhance(1.15)).enhance(1.08)
    lienzo = Image.new('RGB', (W, H), (25, 4, 8))
    lienzo.paste(base.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55)), (0, 0))
    sw = int(W * ancho_sujeto)
    suj = ImageEnhance.Color(_cubrir(Image.open(bg).convert('RGB'), sw, H, foco=foco)).enhance(1.3)
    masc = Image.linear_gradient('L').rotate(90).resize((sw, H))
    if lado == 'izquierda':
        masc = masc.transpose(Image.FLIP_LEFT_RIGHT)
    lienzo.paste(suj, (W - sw, 0), masc.point(lambda v: min(255, int(v * 2.2))))
    return lienzo.convert('RGBA')


def _vineta(lienzo, W, H):
    vig = Image.new('L', (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * .25, -H * .35, W * 1.25, H * 1.35], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    return Image.composite(lienzo, Image.new('RGBA', (W, H), (10, 0, 5, 255)), vig)


def _insignia(lienzo, texto, W, y=36, esc=1.0):
    d = ImageDraw.Draw(lienzo)
    f = _f('teko7_latin.ttf', 70 * esc)
    punto = texto.startswith('●')
    t = texto[1:].strip() if punto else texto
    bw = int(d.textlength(t, font=f)) + int((95 if punto else 60) * esc)
    bx = W - bw - int(36 * esc); alto = int(96 * esc)
    d.rounded_rectangle([bx, y, bx + bw, y + alto], int(22 * esc), fill=(200, 0, 20, 240), outline=(255, 255, 255), width=5)
    if punto:
        r = int(17 * esc)
        d.ellipse([bx + int(26 * esc), y + alto // 2 - r, bx + int(26 * esc) + 2 * r, y + alto // 2 + r], fill=(255, 255, 255))
        d.text((bx + int(72 * esc), y + int(4 * esc)), t, font=f, fill=(255, 255, 255), stroke_width=1)
    else:
        d.text((bx + int(30 * esc), y + int(4 * esc)), t, font=f, fill=(255, 255, 255), stroke_width=1)


def _pastilla(lienzo, texto, x, y_base, W, esc=1.0, acento=(255, 120, 0), tam=86, ancho_max=None):
    f = _f('teko7_latin.ttf', tam * esc)
    lay = _texto(texto, f, relleno='blanco', borde=int(7 * esc), brillo=False, pad=int(24 * esc))
    if ancho_max and lay.width > ancho_max:
        f = _f('teko7_latin.ttf', tam * esc * ancho_max / lay.width)
        lay = _texto(texto, f, relleno='blanco', borde=int(7 * esc), brillo=False, pad=int(24 * esc))
    pill = Image.new('RGBA', (lay.width + int(20 * esc), lay.height - int(10 * esc)), acento + (235,))
    lienzo.alpha_composite(pill, (x, y_base - pill.height))
    lienzo.alpha_composite(lay, (x + int(10 * esc), y_base - lay.height + int(5 * esc)))


def _titular(lienzo, lineas, x, y, ancho_max, tam):
    for ln in lineas:
        lay = _texto(ln, _f('rozha_deva.ttf', tam), borde=int(tam * 0.065))
        if lay.width > ancho_max:
            lay = _texto(ln, _f('rozha_deva.ttf', tam * ancho_max / lay.width), borde=int(tam * 0.065))
        lienzo.alpha_composite(lay, (x, y)); y += lay.height - int(tam * 0.26)
    return y


def portada_larga(bg, lineas, sub, badge, salida):
    """1280x720: Ganesha a la derecha, titular devanagari dorado, pastilla inferior y insignia."""
    W, H = 1280, 720
    L = _fondo(bg, W, H, 0.78)
    L.alpha_composite(_rayos((W, H), (int(W * 0.72), int(H * 0.42))))
    L = _vineta(L, W, H)
    tam = 190 if len(lineas) == 1 else 150
    _titular(L, lineas, 20, 70, W * 0.62, tam)
    _pastilla(L, sub, 40, H - 50, W, ancho_max=W * 0.75)
    if badge:
        _insignia(L, badge, W)
    L.convert('RGB').save(salida, quality=92)
    return salida


def portada_short(bg, lineas, sub, badge, salida):
    """1080x1920 (vertical): Ganesha arriba, titular grande al centro-bajo."""
    W, H = 1080, 1920
    base = _cubrir(Image.open(bg).convert('RGB'), W, H, foco=(0.5, 0.35))
    base = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(base).enhance(1.35)).enhance(1.15)).enhance(1.05)
    L = base.convert('RGBA')
    L.alpha_composite(_rayos((W, H), (W // 2, int(H * 0.30)), alpha=55))
    # degradado oscuro inferior para leer el texto
    sombra = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sombra)
    for y in range(int(H * 0.45), H):
        t = (y - H * 0.45) / (H * 0.55)
        d.line([(0, y), (W, y)], fill=(10, 0, 5, int(235 * min(1, t * 1.3))))
    L.alpha_composite(sombra)
    y = _titular(L, lineas, 30, int(H * 0.56), W - 60, 215 if len(lineas) > 1 else 240)
    _pastilla(L, sub, 50, min(H - 150, y + 150), W, esc=1.2, ancho_max=W - 120)
    if badge:
        _insignia(L, badge, W, y=70, esc=1.25)
    L.convert('RGB').save(salida, quality=92)
    return salida


def _ajustar(texto, font, ancho):
    palabras, lineas, act = texto.split(), [], ''
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    for p in palabras:
        prueba = (act + ' ' + p).strip()
        if d.textlength(prueba, font=font) <= ancho:
            act = prueba
        else:
            lineas.append(act); act = p
    if act:
        lineas.append(act)
    return lineas


def tarjeta_letra(card, es_short, salida):
    """PNG transparente con la letra (devanagari + romanizada + significado). Devuelve (ruta, x, y) para overlay."""
    W, H = (1080, 1920) if es_short else (1920, 1080)
    ancho = 960 if es_short else 1560
    t_dev, t_rom, t_sig = (66, 36, 34) if es_short else (58, 31, 29)
    fd, fr, fs = _f('hind7_deva.ttf', t_dev), _f('hind7_latin.ttf', t_rom), _f('hind7_latin.ttf', t_sig)
    pad = 34
    interno = ancho - 2 * pad
    # ajustar cada linea devanagari al ancho (reduce la fuente si no cabe)
    lin_dev = []
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    for ln in card['deva']:
        f, tam = fd, t_dev
        while d0.textlength(ln, font=f) > interno and tam > 30:
            tam -= 2; f = _f('hind7_deva.ttf', tam)
        lin_dev.append((ln, f, tam))
    lin_rom = []
    for ln in card['roman']:
        f, tam = fr, t_rom
        while d0.textlength(ln, font=f) > interno and tam > 18:
            tam -= 1; f = _f('hind7_latin.ttf', tam)
        lin_rom.append((ln, f, tam))
    lin_sig = _ajustar(card['sig'], fs, interno)
    alto = pad * 2
    alto += sum(int(t * 1.55) for _, _, t in lin_dev) + 12
    alto += sum(int(t * 1.45) for _, _, t in lin_rom) + 14
    alto += sum(int(t_sig * 1.4) for _ in lin_sig) + 6
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, ancho - 1, alto - 1], 30, fill=(18, 4, 8, 205), outline=(255, 190, 60, 255), width=4)
    y = pad
    for ln, f, t in lin_dev:
        d.text((ancho // 2, y), ln, font=f, fill=(255, 214, 90), anchor='ma', stroke_width=2, stroke_fill=(40, 8, 0))
        y += int(t * 1.55)
    y += 12
    for ln, f, t in lin_rom:
        d.text((ancho // 2, y), ln, font=f, fill=(255, 255, 255), anchor='ma')
        y += int(t * 1.45)
    y += 14
    for ln in lin_sig:
        d.text((ancho // 2, y), ln, font=fs, fill=(255, 226, 190), anchor='ma')
        y += int(t_sig * 1.4)
    img.save(salida)
    x = (W - ancho) // 2
    y_pos = (1540 - alto) if es_short else (1010 - alto)
    return salida, x, y_pos
