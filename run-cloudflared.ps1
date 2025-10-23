Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-DockerCompose {
    param([string[]]$Arguments)
    $cmd = @('compose','-f','docker-compose.prod.yml') + $Arguments
    & docker @cmd
    if ($LASTEXITCODE -ne 0) {
        throw "Команда docker compose завершилась с кодом $LASTEXITCODE."
    }
}

$tokenInjected = $false
$secureToken = $null
$exitCode = 0
$finalMessage = $null

try {
    if ([string]::IsNullOrWhiteSpace($env:CF_TUNNEL_TOKEN)) {
        $secureToken = Read-Host -Prompt 'Введите CF_TUNNEL_TOKEN' -AsSecureString
        if ($secureToken.Length -le 0) {
            throw 'CF_TUNNEL_TOKEN не задан.'
        }

        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
        try {
            $plainToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        } finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }

        if ([string]::IsNullOrWhiteSpace($plainToken)) {
            throw 'Ошибка преобразования CF_TUNNEL_TOKEN.'
        }

        [Environment]::SetEnvironmentVariable('CF_TUNNEL_TOKEN', $plainToken, 'Process')
        $plainToken = $null
        $tokenInjected = $true
    }

    Write-Host 'Проверяю конфигурацию docker compose...'
    Invoke-DockerCompose @('config') | Out-Null

    Write-Host 'Перезапускаю cloudflared...'
    Invoke-DockerCompose @('up','-d','--force-recreate','cloudflared')

    $successPatterns = @(
        'Registered tunnel connection',
        'Connection registered',
        'Connected to .* protocol=http2'
    )

    Write-Host 'Ожидаю регистрацию туннеля (HTTP/2)...'
    $deadline = (Get-Date).AddSeconds(120)
    $printed = [System.Collections.Generic.HashSet[string]]::new()
    $registered = $false

    while ((Get-Date) -lt $deadline) {
        $logs = & docker compose -f docker-compose.prod.yml logs --no-log-prefix --tail 200 cloudflared 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw 'Не удалось получить логи cloudflared.'
        }

        foreach ($line in $logs) {
            if ([string]::IsNullOrEmpty($line)) { continue }
            if ($printed.Add($line)) {
                Write-Host $line
            }
        }

        $logText = [string]::Join([Environment]::NewLine, $logs)
        foreach ($pattern in $successPatterns) {
            if ($logText -match $pattern) {
                $registered = $true
                break
            }
        }

        if ($registered) { break }
        Start-Sleep -Seconds 2
    }

    if ($registered) {
        $finalMessage = 'OK: tunnel registered (HTTP/2).'
    }
    else {
        throw 'FAIL: TLS handshake blocked (DPI/VPN?).'
    }
}
catch {
    $exitCode = 1
    Write-Error $_.Exception.Message
}
finally {
    if ($secureToken) {
        $secureToken.Dispose()
    }
    if ($tokenInjected) {
        Remove-Item Env:CF_TUNNEL_TOKEN -ErrorAction SilentlyContinue
    }

    if ($finalMessage) {
        Write-Host $finalMessage
    }
}

exit $exitCode
