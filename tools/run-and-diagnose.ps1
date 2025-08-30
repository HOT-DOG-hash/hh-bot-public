param(
  [switch]$Rebuild,      # выполнить docker compose build web bot
  [switch]$NoCache,      # вместе с -Rebuild использовать --no-cache
  [int]$TimeoutSec = 120,
  [int]$Tail = 200,
  [switch]$SaveLogs      # сохранить логи в .diagnostics\<timestamp>
)

# ---------- ПУТИ ----------
$RepoRoot   = "C:\git-public\hh-bot-public"
$ComposeYml = Join-Path $RepoRoot "docker-compose.yml"
$EnvPath    = Join-Path $RepoRoot ".env"
$Entrypoint = Join-Path $RepoRoot "HH бот\bot\entrypoint.sh"
$RunnerPy   = Join-Path $RepoRoot "HH бот\bot\runner.py"

# ---------- ХЕЛПЕРЫ ----------
function Fail($msg){ Write-Error $msg; exit 1 }
function Check-Cmd($name){ & $name --version *>$null; if($LASTEXITCODE -ne 0){ Fail "Не найдено: $name" } }

function Read-DotEnv($Path){
  $map=@{}
  if(Test-Path $Path){
    (Get-Content -Raw -Encoding UTF8 $Path) -split "`n" | ForEach-Object {
      $line = $_.Trim()
      if($line -and -not $line.StartsWith("#") -and $line -match '^[A-Za-z_][A-Za-z0-9_]*='){
        $k,$v = $line -split '=',2
        $map[$k] = $v
      }
    }
  }
  $map
}

function Get-ContainerId($service){
  $id = (docker compose -f "$ComposeYml" ps -q $service).Trim()
  return $id
}

function Get-Health($cid){
  if(-not $cid){ return "missing" }
  $fmt='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}'
  $out = docker inspect --format $fmt $cid 2>$null
  if($LASTEXITCODE -ne 0){ return "unknown" }
  return $out.Trim()
}

function Wait-Healthy($services, $timeoutSec){
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  $status = @{}
  do{
    foreach($s in $services){
      $cid = Get-ContainerId $s
      $status[$s] = Get-Health $cid
    }
    $allOk = ($status.Values | ForEach-Object { $_ -eq "healthy" } | Where-Object {$_ -eq $true}).Count -eq $services.Count
    if($allOk){ return $true }
    Start-Sleep -Seconds 3
  } while((Get-Date) -lt $deadline)
  Write-Warning "Не дождались здоровья: $($status.GetEnumerator() | ForEach-Object { ""$($_.Key)=$($_.Value)"" } -join ', ')"
  return $false
}

function Save-Logs($dir, $tail){
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  docker compose -f "$ComposeYml" ps           | Out-File -FilePath (Join-Path $dir "ps.txt") -Encoding utf8
  docker compose -f "$ComposeYml" config       | Out-File -FilePath (Join-Path $dir "config.yml") -Encoding utf8
  docker compose -f "$ComposeYml" logs --no-color --tail $tail `
    | Out-File -FilePath (Join-Path $dir "compose.log") -Encoding utf8
  foreach($s in @("db","cache","web","bot","nginx")){
    docker compose -f "$ComposeYml" logs --no-color --tail $tail $s `
      | Out-File -FilePath (Join-Path $dir "$s.log") -Encoding utf8
  }
  Write-Host "Логи сохранены: $dir"
}

# ---------- ПРОВЕРКИ ОКРУЖЕНИЯ ----------
Check-Cmd docker
docker compose version *>$null
if($LASTEXITCODE -ne 0){ Fail "Не найден docker compose v2" }

if(-not (Test-Path $ComposeYml)){ Fail "Нет файла: $ComposeYml" }
if(-not (Test-Path $EnvPath)){   Fail "Нет файла: $EnvPath" }
if(-not (Test-Path $Entrypoint)){Fail "Нет файла: $Entrypoint" }
if(-not (Test-Path $RunnerPy)){  Fail "Нет файла: $RunnerPy" }

# .env базовые проверки (НЕ правим, только предупреждаем)
$envRaw = Get-Content -Raw -Encoding UTF8 $EnvPath
if($envRaw -match "`r"){ Write-Warning ".env содержит CR (Windows-строки). В контейнере у тебя стоит sed, он их уберёт на лету." }
$envMap = Read-DotEnv $EnvPath
if(-not $envMap.ContainsKey("TELEGRAM_BOT_TOKEN") -or -not $envMap["TELEGRAM_BOT_TOKEN"]){
  Fail "В .env нет TELEGRAM_BOT_TOKEN (или он пустой)."
}

# Валидация compose
docker compose -f "$ComposeYml" config *>$null
if($LASTEXITCODE -ne 0){ Fail "docker compose config завершился с ошибкой" }
Write-Host "✅ docker compose config — OK"

# ---------- СБОРКА/ЗАПУСК ----------
Push-Location $RepoRoot
if($Rebuild){
  $args=@("build")
  if($NoCache){ $args += "--no-cache" }
  $args += @("web","bot")
  docker compose -f "$ComposeYml" @args
  if($LASTEXITCODE -ne 0){ Pop-Location; Fail "Сборка завершилась с ошибкой" }
}
docker compose -f "$ComposeYml" up -d
if($LASTEXITCODE -ne 0){ Pop-Location; Fail "docker compose up -d завершился с ошибкой" }

# ---------- ОЖИДАНИЕ ЗДОРОВЬЯ ----------
$ok = Wait-Healthy @("db","cache","web","bot") $TimeoutSec
docker compose -f "$ComposeYml" ps

# ---------- БЫСТРЫЕ ДИАГНОСТИКИ ----------
Write-Host "`n--- Диагностика web (локальное соединение в контейнере) ---"
docker compose -f "$ComposeYml" exec -T web python -c "import os,socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', int(os.getenv('WEB_PORT','8000')))); print('WEB_OK'); s.close()" 2>$null

Write-Host "`n--- Диагностика bot процесса (ищем runner.py) ---"
# Без pgrep/procps: читаем командные строки из /proc
$botCmd = "for p in /proc/[0-9]*/cmdline; do tr '\0' ' ' < ""\$p"" 2>/dev/null; echo; done | grep -F 'bot/runner.py' || true"
docker compose -f "$ComposeYml" exec -T bot sh -lc "$botCmd"

Write-Host "`n--- Проверка /app/.env в контейнере bot на CR ---"
$crCheck = "[ -f /app/.env ] || { echo 'NO_/app/.env'; exit 0; }; tr -d '\r' < /app/.env | cmp -s - /app/.env && echo OK_LF || echo CR_FOUND"
docker compose -f "$ComposeYml" exec -T bot sh -lc "$crCheck"

Write-Host "`n--- Логи (последние $Tail строк) ---"
docker compose -f "$ComposeYml" logs --tail $Tail db cache web bot

# Сохранение логов по желанию
if($SaveLogs){
  $diag = Join-Path $RepoRoot (".diagnostics\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
  Save-Logs $diag $Tail
}

Pop-Location

if(-not $ok){ exit 2 } else { Write-Host "`n🎉 Всё поднялось (или почти). Смотри вывод выше." }
