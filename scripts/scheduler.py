import schedule, time, subprocess, sys
from datetime import datetime

def log(msg):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{hora}] {msg}")
    with open('C:/SpiritualWave/logs/scheduler.log', 'a', encoding='utf-8') as f:
        f.write(f"[{hora}] {msg}\n")

contador = [4]

def producir_y_subir():
    num = contador[0]
    contador[0] += 1
    log(f"Iniciando video #{num}...")
    try:
        subprocess.run([sys.executable, 'scripts/pipeline.py', str(num)])
        subprocess.run([sys.executable, 'scripts/subir_auto.py', str(num)])
        log(f"Video #{num} publicado OK")
    except Exception as e:
        log(f"ERROR: {e}")

schedule.every().day.at("09:00").do(producir_y_subir)
schedule.every().day.at("13:00").do(producir_y_subir)
schedule.every().day.at("19:00").do(producir_y_subir)

log("Scheduler activo — 3 videos/dia a las 9am, 1pm, 7pm")

while True:
    schedule.run_pending()
    time.sleep(30)