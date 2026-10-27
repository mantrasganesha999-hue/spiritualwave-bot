import os, requests
from datetime import datetime
import notificar

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')

POSTS = [
    "Buenos dias! Que mantra o musica de Ganesha te acompana hoy? Cuentanos abajo 🙏",
    "Pregunta del dia: que significa Ganesha para ti en tu practica diaria? Te leemos en los comentarios 🕉",
    "Cuando prefieres escuchar musica devocional: por la manana, por la tarde o antes de dormir? 🎵",
    "Desde que pais nos escuchas hoy? Cuentanos en los comentarios 🌍",
    "Que bhajan o mantra de Ganesha te gustaria escuchar en un proximo video? 🙏",
    "Una pausa de un minuto para respirar y agradecer. Que agradeces hoy? ✨",
    "Hoy transmitimos en vivo musica devocional de Ganesha a las 10:00 a. m. (Colombia). Activa el recordatorio 🔔",
    "Comparte este canal con alguien a quien le guste la musica devocional 💫",
    "Que momento del dia es tu favorito para la musica de meditacion? 🕉",
    "Gracias por acompanarnos. Cuentanos como usas la musica de Ganesha: estudio, trabajo, descanso o puja 🙏",
]

import random
post = random.choice(POSTS)
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

notificar.post_comunidad(post)
print(f"Post enviado a Telegram: {post[:60]}...")