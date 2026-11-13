# Corre sola cada 20 minutos. Para cada video en contenido\ que aun no se subio:
# toma las imagenes que guardaste en su carpeta imagenes\ (con cualquier nombre), las ordena por el orden en que
# las guardaste, las renombra 01, 02, 03... y, cuando estan todas, las sube a GitHub para que el video se monte solo.
Set-Location C:\SpiritualWave
$log = 'C:\SpiritualWave\logs\vigilar.log'
New-Item -ItemType Directory -Force C:\SpiritualWave\logs | Out-Null
function L($t) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm') $t" | Out-File $log -Append -Encoding utf8 }
foreach ($c in Get-ChildItem contenido -Directory) {
    $guion = Join-Path $c.FullName 'guion.json'
    if (-not (Test-Path $guion) -or (Test-Path (Join-Path $c.FullName 'subido.json'))) { continue }
    $carpImg = Join-Path $c.FullName 'imagenes'
    New-Item -ItemType Directory -Force $carpImg | Out-Null
    $g = Get-Content $guion -Raw -Encoding UTF8 | ConvertFrom-Json
    $nesc = @($g.escenas).Count
    $imgs = @(Get-ChildItem $carpImg -File | Where-Object { $_.Extension -match '^\.(png|jpe?g|webp)$' } | Sort-Object LastWriteTime, Name)
    if ($imgs.Count -eq 0) { continue }
    # renombrar en orden si hace falta (las que no se llaman 01, 02...)
    $todasNumeradas = ($imgs | Where-Object { $_.BaseName -notmatch '^\d{2}$' }).Count -eq 0
    if (-not $todasNumeradas) {
        $k = 0
        foreach ($f in $imgs) { $k++; Rename-Item $f.FullName ("tmp_{0:D2}{1}" -f $k, $f.Extension.ToLower()) }
        foreach ($f in Get-ChildItem $carpImg -File -Filter 'tmp_*') { Rename-Item $f.FullName ($f.Name -replace '^tmp_', '') }
        L "$($c.Name): $($imgs.Count) imagenes renombradas en orden"
    }
    $imgs = @(Get-ChildItem $carpImg -File | Where-Object { $_.BaseName -match '^\d{2}$' })
    if ($imgs.Count -lt $nesc) { L "$($c.Name): $($imgs.Count) de $nesc imagenes, espero las demas"; continue }
    $cambios = git status --porcelain -- "contenido/$($c.Name)"
    if (-not $cambios) { continue }
    git add "contenido/$($c.Name)" 2>&1 | Out-Null
    git commit -m "Video nuevo: $($c.Name) (imagenes listas)" 2>&1 | Out-Null
    git pull --rebase --autostash -q origin master 2>&1 | Out-Null
    $r = git push -q origin master 2>&1
    if ($LASTEXITCODE -eq 0) { L "$($c.Name): SUBIDO a GitHub, se monta solo" } else { L "$($c.Name): error al subir: $r" }
}
