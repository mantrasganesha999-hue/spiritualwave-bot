"""Muestra si los ultimos directos de verdad salieron en vivo (estado, hora real de inicio/fin, vistas).

Uso (PowerShell, desde C:\\SpiritualWave):  python scripts\\estado_directos.py
Cuesta 2 unidades de cuota.
"""
import os, pickle
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cot(texto):
    if not texto:
        return '-'
    return (datetime.strptime(texto[:19], '%Y-%m-%dT%H:%M:%S') - timedelta(hours=5)).strftime('%d %H:%M')


def main():
    from googleapiclient.discovery import build
    with open(os.path.join(BASE, 'token.pickle'), 'rb') as f:
        yt = build('youtube', 'v3', credentials=pickle.load(f))
    r = yt.liveBroadcasts().list(part='id,snippet,status', broadcastStatus='all', maxResults=8).execute()
    items = r.get('items', [])
    if not items:
        print("No hay directos.")
        return
    det = {v['id']: v for v in yt.videos().list(
        part='liveStreamingDetails,statistics', id=','.join(b['id'] for b in items)).execute().get('items', [])}
    print(f"{'inicio real':<12} {'fin real':<10} {'estado':<10} {'vistas':>7}  titulo / id")
    for b in items:
        d = det.get(b['id'], {})
        ls = d.get('liveStreamingDetails', {})
        views = d.get('statistics', {}).get('viewCount', '?')
        print(f"{cot(ls.get('actualStartTime')):<12} {cot(ls.get('actualEndTime')):<10} "
              f"{b['status']['lifeCycleStatus']:<10} {views:>7}  {b['snippet']['title'][:38]}  {b['id']}")
    print("\n'inicio real' = '-' significa que YouTube NUNCA lo marco en vivo.")


if __name__ == '__main__':
    main()
