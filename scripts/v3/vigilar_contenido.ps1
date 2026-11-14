# Corre sola cada 20 minutos. Para cada video en contenido\ que aun no se subio:
#  - imagenes\ : imagenes o videos cortos con cualquier nombre -> se ordenan por el orden en que los guardaste (01, 02...)
#  - musica\   : las canciones de Suno (MP3) con cualquier nombre
# Cuando hay algo nuevo y la carpeta esta completa, se sube a GitHub y el video se monta solo a las 3:05 am.
Set-Location C:\SpiritualWave
$log = 'C:\SpiritualWave\logs\vigilar.log'
New-Item -ItemType Directory -Force C:\SpiritualWave\logs | Out-Null
function L($t) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm') $t" | Out-File $log -Append -Encoding utf8 }
foreach ($c in Get-ChildItem contenido -Directory) {
    $guion = Join-Path $c.FullName 'guion.json'
    if (-not (Test-Path $guion) -or (Test-Path (Join-Path $c.FullName 'subido.json'))) { continue }
    $carpImg = Join-Path $c.FullName 'imagenes'; New-Item -ItemType Directory -Force $carpImg | Out-Null
    $carpMus = Join-Path $c.FullName 'musica';   New-Item -ItemType Directory -Force $carpMus | Out-Null
    $g = Get-Content $guion -Raw -Encoding UTF8 | ConvertFrom-Json
    $necesita = @($g.escenas | Where-Object { $_.tipo -ne 'cancion' }).Count
    $llevaCancion = @($g.escenas | Where-Object { $_.tipo -eq 'cancion' }).Count -gt 0
    $imgs = @(Get-ChildItem $carpImg -File | Where-Object { $_.Extension -match '^\.(png|jpe?g|webp|mp4|mov|webm|m4v)$' } | Sort-Object LastWriteTime, Name)
    $songs = @(Get-ChildItem $carpMus -File | Where-Object { $_.Extension -match '^\.(mp3|wav|m4a|flac|ogg)$' })
    if ($imgs.Count -gt 0 -and ($imgs | Where-Object { $_.BaseName -notmatch '^\d{2}$' })) {
        $k = 0
        foreach ($f in $imgs) { $k++; Rename-Item $f.FullName ("tmp_{0:D2}{1}" -f $k, $f.Extension.ToLower()) }
        foreach ($f in Get-ChildItem $carpImg -File -Filter 'tmp_*') { Rename-Item $f.FullName ($f.Name -replace '^tmp_', '') }
        L "$($c.Name): $($imgs.Count) imagenes/videos ordenados"
    }
    if ($imgs.Count -gt 0 -and $imgs.Count -lt $necesita) { L "$($c.Name): $($imgs.Count) de $necesita imagenes/videos, espero las demas"; continue }
    if ($llevaCancion -and $songs.Count -eq 0) { continue }
    $cambios = git status --porcelain -- "contenido/$($c.Name)"
    if (-not $cambios) { continue }
    git add "contenido/$($c.Name)" 2>&1 | Out-Null
    git commit -m "Video nuevo: $($c.Name) (material listo)" 2>&1 | Out-Null
    git pull --rebase --autostash -q origin master 2>&1 | Out-Null
    $r = git push -q origin master 2>&1
    if ($LASTEXITCODE -eq 0) { L "$($c.Name): SUBIDO a GitHub, se monta a las 3:05 am" } else { L "$($c.Name): error al subir: $r" }
}

# Musica de fondo (instrumentales de Suno para katha y guias): assets\music_fondo
$fondo = git status --porcelain -- "assets/music_fondo"
if ($fondo) {
    git add "assets/music_fondo" 2>&1 | Out-Null
    git commit -m "Musica de fondo nueva (Suno)" 2>&1 | Out-Null
    git pull --rebase --autostash -q origin master 2>&1 | Out-Null
    $r = git push -q origin master 2>&1
    if ($LASTEXITCODE -eq 0) { L "music_fondo: SUBIDA a GitHub" } else { L "music_fondo: error al subir: $r" }
}
