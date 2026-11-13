# Tarea nocturna de SpiritualWave (corre sola a las 3:30 am, despues de que se renueva la cuota a las 3:00).
# Reserva cuota para que los videos nuevos se puedan subir de dia (~1,700 unidades cada uno).
# 1) Titulos nuevos (120 por noche). 2) Privatizar con candado de horas: 40 mientras haya titulos pendientes, luego 150.
Set-Location C:\SpiritualWave
$env:PYTHONIOENCODING = 'utf-8'
$py = 'C:\SpiritualWave\env\Scripts\python.exe'
$log = 'C:\SpiritualWave\logs\privatizar_diario.log'
New-Item -ItemType Directory -Force C:\SpiritualWave\logs | Out-Null
"===== $(Get-Date -Format 'yyyy-MM-dd HH:mm') =====" | Out-File $log -Append -Encoding utf8
$aplicados = 0
if (Test-Path 'titulos_log.csv') { $aplicados = @(Import-Csv 'titulos_log.csv' | Where-Object { $_.accion -eq 'aplicado' } | Select-Object -ExpandProperty video_id -Unique).Count }
$maxPriv = if ($aplicados -lt 700) { 40 } else { 150 }
foreach ($paso in @(@('scripts\aplicar_titulos.py', '120'), @('scripts\privatizar_lote.py', "$maxPriv"))) {
    "--- $($paso[0]) (max $($paso[1])) ---" | Out-File $log -Append -Encoding utf8
    for ($i = 1; $i -le 4; $i++) {
        & $py $paso[0] --ejecutar --max $paso[1] 2>&1 | ForEach-Object { "$_" } | Out-File $log -Append -Encoding utf8
        if ($LASTEXITCODE -eq 0) { break }
        "Intento $i fallo (codigo $LASTEXITCODE). Reintento en 2 minutos." | Out-File $log -Append -Encoding utf8
        Start-Sleep -Seconds 120
    }
}
"===== fin $(Get-Date -Format 'HH:mm') =====" | Out-File $log -Append -Encoding utf8
