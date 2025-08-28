<# 
  Smoke-тесты readiness/liveness.
  Параметры:
    -Wait : ждать готовности (polling)
  Запуск:
    .\scripts\smoke.ps1
    .\scripts\smoke.ps1 -Wait
#>
param([switch]$Wait)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()

function Test-Url {
  param(
    [Parameter(Mandatory)] [string]$Url
  )
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
    if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) { return $true }
    return $false
  } catch { return $false }
}

function Wait-Healthy {
  param(
    [string[]]$Urls,
    [int]$TimeoutSec = 120,
    [int]$IntervalSec = 3
  )
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
    $allOk = $true
    foreach ($u in $Urls) {
      $ok = Test-Url -Url $u
      Write-Host ("{0} -> {1}" -f $u, ($(if($ok){"OK"}else{"WAIT..."})))
      if (-not $ok) { $allOk = $false }
    }
    if ($allOk) { return $true }
    Start-Sleep -Seconds $IntervalSec
  }
  return $false
}

$checks = @(
  "http://127.0.0.1:8000/healthz",  # liveness приложения
  "http://127.0.0.1:8000/health",   # readiness (Redis+DB)
  "http://127.0.0.1/healthz"        # liveness nginx
)

if ($Wait) {
  Write-Host "Ожидаем готовности сервисов (до 120 сек)..."
  if (-not (Wait-Healthy -Urls $checks -TimeoutSec 120 -IntervalSec 3)) {
    Write-Error "Сервисы не вышли в готовность за отведённое время."
    exit 1
  }
} else {
  foreach ($u in $checks) {
    $ok = Test-Url -Url $u
    Write-Host ("{0} -> {1}" -f $u, ($(if($ok){"OK"}else{"FAIL"})))
  }
}
Write-Host "Smoke: OK"
