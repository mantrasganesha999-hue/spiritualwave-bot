# Sube YA un video (sin esperar a la tarea de cada 20 min).  Uso: powershell -ExecutionPolicy Bypass -File scripts\v3\subir_video.ps1
Set-Location C:\SpiritualWave
& powershell -NoProfile -ExecutionPolicy Bypass -File C:\SpiritualWave\scripts\v3\vigilar_contenido.ps1
Get-Content C:\SpiritualWave\logs\vigilar.log -Tail 5
