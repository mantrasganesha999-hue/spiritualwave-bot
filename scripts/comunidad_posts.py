import os, requests
from datetime import datetime
import notificar

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.environ.get('TELEGRAM_CHAT_ID')

POSTS = [
    "🔱 Buenos dias! Que mantra de Ganesha escuchas hoy para atraer abundancia? Cuentanos abajo 🙏✨",
    "💫 PREGUNTA DEL DIA: Si Ganesha te concediera UN deseo hoy, cual seria? Escribelo en los comentarios 🕉🔱",
    "🌟 Tip espiritual: Repite 108 veces OM GAN GANAPATAYE NAMAHA antes de dormir y observa los cambios 🙏",
    "⚡ Cual es tu frecuencia favorita para meditar? 528hz, 432hz o 963hz? Vota en los comentarios 🎵✨",
    "🔥 El secreto de Ganesha: La abundancia llega cuando dejas de pedir y empiezas a agradecer 🙏🌸",
    "💎 RETO 21 DIAS: Escucha un mantra de Ganesha cada manana por 21 dias. Quien se une? 🔱",
    "🌙 Antes de dormir: Pon un mantra de Ganesha. Tu subconsciente manifestara mientras duermes ✨",
    "🕉 Dato sagrado: El numero 108 es sagrado en el hinduismo. Sabias esto? 🔱",
    "🙏 Comparte este canal con alguien que necesite paz y abundancia hoy 💫",
    "⚡ Como te sientes despues de escuchar mantras de Ganesha? Cuentanos 🔱",
]

import random
post = random.choice(POSTS)
fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

notificar.post_comunidad(post)
print(f"Post enviado a Telegram: {post[:60]}...")