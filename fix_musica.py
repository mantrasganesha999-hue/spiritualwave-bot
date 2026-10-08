import os

content = open('scripts/pipeline_cloud.py', encoding='utf-8').read()

old = '''def get_musicas():
    todas = []
    for i in range(1, 22):
        p = os.path.join(BASE, f'assets/music/suno_{i}.mp3')
        if os.path.exists(p):
            todas.append(p)
    for i in range(1, 4):
        p = os.path.join(BASE, f'assets/music/mezcla_{i}.mp3')
        if os.path.exists(p):
            todas.append(p)
            todas.append(p)
    return todas'''

new = '''def get_musicas():
    folder = os.path.join(BASE, 'assets/music')
    todas = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith('.mp3')
    ]
    return todas'''

if old in content:
    content = content.replace(old, new)
    open('scripts/pipeline_cloud.py', 'w', encoding='utf-8').write(content)
    print('Fix musica OK')
else:
    print('Texto no encontrado')