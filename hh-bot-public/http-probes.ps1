param(
  [string]$HostHeader = "www.hhoffer.ru",
  [string]$User = "",
  [string]$Pass = ""
)
$ErrorActionPreference='Continue'
Write-Host "== HTTP(S) probes ==" -ForegroundColor Cyan

function Show-Head([string]$url,[switch]$Auth,[switch]$Local){
  $args = @("-sSI","--max-time","5")
  if($Local){ $args += @("-H","Host: $HostHeader") }
  if($Auth -and $User){ $args = @("-u","$User`:$Pass") + $args }
  $args += $url
  & curl @args 2>$null | Select-Object -First 12 | Out-Host
  "" | Out-Host
}

Write-Host "-- local http (Host header) /healthz" -ForegroundColor DarkGray
Show-Head "http://127.0.0.1/healthz" -Local

Write-Host "-- local http (Host header) /admin (no auth)" -ForegroundColor DarkGray
Show-Head "http://127.0.0.1/admin/" -Local

Write-Host "-- local http (Host header) /admin (with auth)" -ForegroundColor DarkGray
Show-Head "http://127.0.0.1/admin/" -Local -Auth:($User -ne "")

Write-Host "-- external http(s) /healthz" -ForegroundColor DarkGray
Show-Head "http://$HostHeader/healthz"
Show-Head "https://$HostHeader/healthz"

Write-Host "-- external /admin (no auth)" -ForegroundColor DarkGray
Show-Head "http://$HostHeader/admin/"
Show-Head "https://$HostHeader/admin/"

Write-Host "-- external /admin (with auth)" -ForegroundColor DarkGray
Show-Head "http://$HostHeader/admin/" -Auth:($User -ne "")
Show-Head "https://$HostHeader/admin/" -Auth:($User -ne "")
