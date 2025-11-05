$ports=@(80,443)
foreach($p in $ports){
  Write-Host "`n== Port $p ==" -ForegroundColor Cyan
  $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
  if(-not $conns){ Write-Host "свободен"; continue }
  $conns | ForEach-Object{
    $pid=$_.OwningProcess
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    [pscustomobject]@{Port=$p; PID=$pid; Process=$proc.Name; Path=$proc.Path}
  } | Format-Table -AutoSize
}
