# Busca tus carpetas de clips de Ganesha y las copia al proyecto (sin duplicados, solo videos de hasta 95 MB).
#   horizontales -> assets\videos_ganesha_horizontal   (videos largos)
#   verticales   -> assets\videos_ganesha              (Shorts)
Set-Location C:\SpiritualWave
$buscar = @("$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Documents", "$env:USERPROFILE\Videos", "$env:USERPROFILE\OneDrive", "$env:USERPROFILE")
function Encontrar($nombre) {
    foreach ($b in $buscar) {
        if (-not (Test-Path $b)) { continue }
        $d = Get-ChildItem $b -Directory -Recurse -Depth 4 -Filter $nombre -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike 'C:\SpiritualWave*' } | Select-Object -First 1
        if ($d) { return $d.FullName }
    }
    return $null
}
$total = 0
foreach ($par in @(@('imagenes_ganesha_horizontales', 'assets\videos_ganesha_horizontal', 'gh2_'), @('imagenes_ganesha', 'assets\videos_ganesha', 'gv2_'))) {
    $origen = Encontrar $par[0]
    if (-not $origen) { Write-Host "No encontre la carpeta '$($par[0])'" -ForegroundColor Yellow; continue }
    $dest = $par[1]; New-Item -ItemType Directory -Force $dest | Out-Null
    $hashes = @{}
    Get-ChildItem $dest -File | ForEach-Object { $hashes[(Get-FileHash $_.FullName -Algorithm MD5).Hash] = 1 }
    $vids = Get-ChildItem $origen -File -Recurse | Where-Object { $_.Extension -match '^\.(mp4|mov|webm|m4v)$' }
    $n = 0; $dup = 0; $grandes = 0; $mb = 0
    foreach ($v in $vids) {
        if ($v.Length -gt 95MB) { $grandes++; continue }
        $h = (Get-FileHash $v.FullName -Algorithm MD5).Hash
        if ($hashes.ContainsKey($h)) { $dup++; continue }
        $hashes[$h] = 1; $n++
        Copy-Item $v.FullName (Join-Path $dest ("{0}{1:D3}{2}" -f $par[2], $n, $v.Extension.ToLower()))
        $mb += $v.Length / 1MB
    }
    $total += $mb
    Write-Host ("{0}: {1} videos encontrados en {2}" -f $par[0], $vids.Count, $origen)
    Write-Host ("   copiados {0} nuevos ({1:N0} MB), duplicados {2}, demasiado grandes (>95 MB) {3}" -f $n, $mb, $dup, $grandes) -ForegroundColor Green
}
Write-Host ("Total nuevo: {0:N0} MB" -f $total)
