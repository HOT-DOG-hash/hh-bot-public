param([Parameter(Mandatory=$true)][string]$HostName)

Write-Host "== Probing with Host: $HostName ==" -ForegroundColor Cyan
try { curl -I -H "Host: $HostName" http://127.0.0.1/healthz } catch { Write-Warning $_ }
try { curl -I -H "Host: $HostName" http://127.0.0.1/admin/ }  catch { Write-Warning $_ }
try { curl -I -H "Host: $HostName" http://127.0.0.1/api/health } catch { Write-Warning $_ }


