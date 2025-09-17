# port80-check.ps1
$ErrorActionPreference = 'Continue'
Write-Host "== Port 80 listeners on host ==" -ForegroundColor Cyan

try {
  $conns = Get-NetTCPConnection -LocalPort 80 -State Listen -ErrorAction Stop
  if ($conns) {
    $conns | Select-Object LocalAddress,LocalPort,OwningProcess,State | Format-Table -AutoSize | Out-Host
    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    if ($pids) { Get-Process -Id $pids | Select-Object Id,ProcessName | Format-Table -AutoSize | Out-Host }
  } else { "Никто не слушает порт 80 (или нужны права администратора)." | Out-Host }
} catch {
  Write-Warning "Get-NetTCPConnection недоступен/нет прав. Пробую netstat:"
  netstat -ano | Select-String ":80\s+LISTEN" | Out-Host
}
