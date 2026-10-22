"""Borra directos viejos que quedaron en 'created/ready/testing' sin emitirse (nunca toca uno en vivo).

Uso (PowerShell, desde C:\\SpiritualWave):  python scripts\\limpiar_directos.py
Cuesta ~50 unidades de cuota por directo borrado.
"""
import os, pickle

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    from googleapiclient.discovery import build
    with open(os.path.join(BASE, 'token.pickle'), 'rb') as f:
        yt = build('youtube', 'v3', credentials=pickle.load(f))
    r = yt.liveBroadcasts().list(part='id,snippet,status', broadcastStatus='all', maxResults=50).execute()
    n = 0
    for b in r.get('items', []):
        est = b['status']['lifeCycleStatus']
        if est in ('created', 'ready', 'testing'):
            yt.liveBroadcasts().delete(id=b['id']).execute()
            n += 1
            print(f"  borrado {b['id']} ({est}) {b['snippet']['title'][:40]}")
        else:
            print(f"  se deja   {b['id']} ({est}) {b['snippet']['title'][:40]}")
    print(f"\nBorrados: {n}")


if __name__ == '__main__':
    main()
