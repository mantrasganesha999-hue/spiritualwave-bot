# Sube a GitHub un video nuevo (su carpeta en contenido\) para que se monte y programe solo.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\v3\subir_video.ps1 01_janm
param([Parameter(Mandatory=$true)][string]$id)
Set-Location C:\SpiritualWave
$c = "contenido\$id"
if (-not (Test-Path "$c\guion.json")) { Write-Host "No existe $c\guion.json" -ForegroundColor Red; exit 1 }
$g = Get-Content "$c\guion.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$falta = @()
foreach ($e in $g.escenas) {
  $n = '{0:D2}' -f [int]$e.n
  if (-not (Get-ChildItem "$c\imagenes\$n.*" -ErrorAction SilentlyContinue)) { $falta += $n }
}
if ($falta.Count -gt 0) { Write-Host "Faltan imagenes: $($falta -join ', ')  (en $c\imagenes\)" -ForegroundColor Yellow; exit 1 }
Write-Host "OK: $($g.escenas.Count) imagenes listas para $id" -ForegroundColor Green
git add "$c"
git commit -m "Video nuevo: $id" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" | Out-Null
git push origin master
Write-Host "Subido. GitHub lo monta y lo programa solo; te llega el enlace por Telegram (unos 15-25 min)." -ForegroundColor Green
