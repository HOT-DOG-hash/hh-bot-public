Param(
  [string]$AppPath = "C:\git-public\hh-bot-public\HH бот",
  [string]$Pydantic = "2.7.4"
)

# Ищем все requirements.txt в папке приложения (и, если что, в корне репо)
$files = Get-ChildItem -LiteralPath $AppPath -Filter requirements.txt -Recurse -File -ErrorAction SilentlyContinue
if (-not $files) {
  $repoRoot = Split-Path $AppPath -Parent
  $files = Get-ChildItem -LiteralPath $repoRoot -Filter requirements.txt -Recurse -File -ErrorAction SilentlyContinue
}

if (-not $files) { throw "requirements.txt не найден. Проверь структуру проекта." }

foreach($f in $files){
  $raw = Get-Content -LiteralPath $f.FullName -Raw
  if ($raw -match '(?m)^\s*pydantic\s*==') {
    $raw = [regex]::Replace($raw,'(?m)^\s*pydantic\s*==.*$',"pydantic==$Pydantic")
  } else {
    if (-not $raw.EndsWith("`r`n")) { $raw += "`r`n" }
    $raw += "pydantic==$Pydantic`r`n"
  }
  Set-Content -LiteralPath $f.FullName -Value $raw -Encoding UTF8
  Write-Host "Pinned pydantic to $Pydantic -> $($f.FullName)"
}

Set-Location -LiteralPath $AppPath

# Пересобираем без кэша, затем поднимаем
try { docker compose build --no-cache } catch { docker-compose build --no-cache }
try { docker compose up -d } catch { docker-compose up -d }
