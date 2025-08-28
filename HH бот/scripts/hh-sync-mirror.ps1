param(
  [Parameter(Mandatory=$true)] [string]$Source, # путь к исходнику ИЛИ git URL (приватный)
  [string]$Dest = "https://github.com/HOT-DOG-hash/hh-bot-public.git",
  [string[]]$Exclude = @(".env",".env.*","secrets/","*.pem","*.key","*.pfx","*.sqlite","*.db"),
  [switch]$ScrubHistory,  # включить зачистку истории от путей из -Exclude (нужен git-filter-repo)
  [switch]$Force          # жёсткий форс-пуш
)

$ErrorActionPreference="Stop"
function Need($cmd){ if(-not (Get-Command $cmd -ErrorAction SilentlyContinue)){throw "Команда '$cmd' не найдена"}}
Need git

$work = Join-Path $env:TEMP ("hh-sync-"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work | Out-Null
$bare = Join-Path $work "src.git"

if (Test-Path $Source -PathType Container) {
  if (-not (Test-Path (Join-Path $Source ".git"))) { throw "Папка $Source не git-репозиторий" }
  git clone --mirror --no-local "$Source" "$bare"
} else {
  git clone --mirror "$Source" "$bare"
}

Push-Location $bare
try {
  git fetch --all --prune
  if ($ScrubHistory -and $Exclude.Count -gt 0) {
    if (-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)) {
      Write-Warning "git-filter-repo не установлен — пропускаю зачистку истории"
    } else {
      $paths = Join-Path $work "paths.txt"
      $Exclude | Set-Content -Encoding UTF8 $paths
      git filter-repo --path-glob :regex --invert-paths --paths-from-file "$paths"
    }
  }

  $destUrl = $Dest
  if ($destUrl -match "^https://") {
    if ($env:GITHUB_TOKEN) {
      $destUrl = $destUrl -replace "^https://","https://$($env:GITHUB_TOKEN)@"
      Write-Host "Использую GITHUB_TOKEN из окружения"
    }
  }

  git remote remove mirror 2>$null | Out-Null
  git remote add mirror "$destUrl"
  $flags = @("--prune", ($Force ? "--force" : "--force-with-lease"))
  git push @flags mirror --mirror
  Write-Host "Готово ✅"
}
finally { Pop-Location }
