"""Agrega etiquetas internas a videos ya subidos (para que el tope diario los cuente).

Uso (PowerShell, desde C:\\SpiritualWave):
    python scripts\\etiquetar_video.py ybAisuITvog sw_en_largo tSiV_vFk-cs sw_en_short
Cada video cuesta 51 unidades de cuota (1 de lectura + 50 de actualizacion).
"""
import os, sys, pickle

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    if len(argv) < 2 or len(argv) % 2:
        print("Uso: etiquetar_video.py ID1 etiqueta1 [ID2 etiqueta2 ...]")
        return 1
    from googleapiclient.discovery import build
    with open(os.path.join(BASE, 'token.pickle'), 'rb') as f:
        yt = build('youtube', 'v3', credentials=pickle.load(f))
    for vid, etiqueta in zip(argv[0::2], argv[1::2]):
        r = yt.videos().list(part='snippet', id=vid).execute()
        if not r.get('items'):
            print(f"  {vid}: no existe")
            continue
        sn = r['items'][0]['snippet']
        tags = sn.get('tags', [])
        if etiqueta in tags:
            print(f"  {vid}: ya tenia {etiqueta}")
            continue
        sn['tags'] = tags + [etiqueta]
        yt.videos().update(part='snippet', body={'id': vid, 'snippet': sn}).execute()
        print(f"  {vid}: + {etiqueta}  ({sn['title'][:50]})")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
