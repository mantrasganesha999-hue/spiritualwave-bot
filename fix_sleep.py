content = open('scripts/pipeline_sleep.py', encoding='utf-8').read()

old = """    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 1500}
    )
    contenido = r.json()['choices'][0]['message']['content']
    descripcion = extraer_campo(contenido, 'DESCRIPCION', 'TAGS') or f"Sleep music video: {titulo}"
    tags = extraer_campo(contenido, 'TAGS') or "#SleepMusic #Ganesha #528hz #Meditation #DeepSleep"
    return limpiar_texto(descripcion), limpiar_texto(tags)"""

new = """    try:
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 1500},
            timeout=30
        )
        data = r.json()
        if 'choices' not in data:
            print(f"Groq error: {data}")
            return "8 Hours Ganesha Sleep Music for deep healing and abundance", "#SleepMusic #Ganesha #528hz #Meditation #DeepSleep"
        contenido = data['choices'][0]['message']['content']
    except Exception as e:
        print(f"Groq exception: {e}")
        return "8 Hours Ganesha Sleep Music for deep healing and abundance", "#SleepMusic #Ganesha #528hz #Meditation #DeepSleep"
    descripcion = extraer_campo(contenido, 'DESCRIPCION', 'TAGS') or f"Sleep music video: {titulo}"
    tags = extraer_campo(contenido, 'TAGS') or "#SleepMusic #Ganesha #528hz #Meditation #DeepSleep"
    return limpiar_texto(descripcion), limpiar_texto(tags)"""

if old in content:
    content = content.replace(old, new)
    open('scripts/pipeline_sleep.py', 'w', encoding='utf-8').write(content)
    print('Fix sleep OK')
else:
    print('Texto no encontrado')