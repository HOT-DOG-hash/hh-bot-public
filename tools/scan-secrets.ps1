<# 
  tools/scan-secrets.ps1 — v2
  - Фикс null input для Regex.Matches
  - Расширен список бинарных расширений (в т.ч. .phar)
  - Починен report-path для Gitleaks (working)
  - Более безопасные проверки и логирование
#>

[CmdletBinding()]
param(
  [string]$OutputDir = "tools/reports",
  [int]$MaxFileSizeMB = 5,
  [switch]$NoDocker,
  [switch]$NoHistory
)

function New-CleanDir($path) {
  if (!(Test-Path $path)) { New-Item -ItemType Directory -Force -Path $path | Out-Null }
}

function Test-Docker {
  if ($NoDocker) { return $false }
  try { return -not [string]::IsNullOrWhiteSpace((docker version --format '{{.Server.Version}}' 2>$null)) } catch { return $false }
}

function Get-RepoRoot {
  try { (git rev-parse --show-toplevel).Trim() } catch { $PWD.Path }
}

$SkipDirs = @('.git','node_modules','venv','.venv','dist','build','__pycache__','.mirror.git','.remote-mirror.git')
$SkipExts = @(
  '.png','.jpg','.jpeg','.gif','.pdf','.ico','.svg',
  '.woff','.woff2','.eot','.ttf','.otf',
  '.zip','.gz','.tar','.7z','.bz2','.xz',
  '.db','.sqlite','.pyc','.phar'  # добавили .phar
)

$Rules = @(
  @{ Name='TelegramBotToken';     Regex='\b[0-9]{6,}:[A-Za-z0-9_-]{30,}\b' },
  @{ Name='JWT';                  Regex='\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b' },
  @{ Name='BearerToken';          Regex='Bearer\s+[A-Za-z0-9-_\.=]{20,}' },
  @{ Name='PrivateKey';           Regex='-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----' },
  @{ Name='AWS_AccessKeyID';      Regex='\bAKIA[0-9A-Z]{16}\b' },
  @{ Name='AWS_SecretKeyVar';     Regex='(?i)AWS_SECRET_ACCESS_KEY|aws[_-]?secret[_-]?access[_-]?key' },
  @{ Name='DatabaseURL';          Regex='(?i)\bpostgres(?:ql)?(?:\+\w+)?:\/\/[^\s"''<>]+' },
  @{ Name='RedisURL';             Regex='(?i)\bredis:\/\/[^\s"''<>]+' },
  @{ Name='GenericSecretKV';      Regex='(?i)\b(SECRET|TOKEN|PASSWORD|PASS|API[_-]?KEY|WEBHOOK|CLIENT[_-]?SECRET|PRIVATE[_-]?KEY)\s*[:=]\s*["''][^"'']{8,}["'']|\b(SECRET|TOKEN|PASSWORD|PASS|API[_-]?KEY|WEBHOOK|CLIENT[_-]?SECRET|PRIVATE[_-]?KEY)\s*[:=]\s*[A-Za-z0-9/_\.\-+=]{12,}' }
)

$AllowValuePatterns = @(
  '(?i)changeme',
  '(?i)dev(-|_)?secret',
  '(?i)dev-not-secret'
)

$Root = Get-RepoRoot
Set-Location $Root
New-CleanDir $OutputDir
$RegexCsv = Join-Path $OutputDir 'regex-findings.csv'
$RegexTxt = Join-Path $OutputDir 'regex-findings.txt'
Remove-Item $RegexCsv,$RegexTxt -ErrorAction SilentlyContinue

$Findings = New-Object System.Collections.Generic.List[object]

Write-Host "== Regex scan (working tree) ==" -ForegroundColor Cyan

$files = Get-ChildItem -Recurse -File | Where-Object {
  foreach ($sd in $SkipDirs) { if ($_.FullName -replace '\\','/' -match "/$sd(/|$)") { return $false } }
  if ($SkipExts -contains $_.Extension.ToLower()) { return $false }
  if (($_.Length / 1MB) -gt $MaxFileSizeMB) { return $false }
  return $true
}

foreach ($file in $files) {
  $text = $null
  try {
    $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop
  } catch {
    continue
  }
  if ([string]::IsNullOrEmpty($text)) { continue }

  foreach ($rule in $Rules) {
    try {
      $matches = [System.Text.RegularExpressions.Regex]::Matches($text, $rule.Regex, 'IgnoreCase, Multiline')
    } catch {
      continue
    }
    if ($matches.Count -eq 0) { continue }

    $lines = $text -split "`r?`n"
    foreach ($m in $matches) {
      if ($m -eq $null -or $m.Value -eq $null) { continue }

      $before = if ($m.Index -gt 0) { $text.Substring(0, $m.Index) } else { "" }
      $lineNumber = ($before -split "`r?`n").Count
      if ($lineNumber -lt 1 -or $lineNumber -gt $lines.Length) { continue }
      $lineText = $lines[$lineNumber-1]

      $allowed = $false
      foreach ($ap in $AllowValuePatterns) { if ($m.Value -match $ap) { $allowed = $true; break } }
      if ($allowed) { continue }

      $val = $m.Value
      $redacted = if ($val.Length -gt 10) { $val.Substring(0,4) + '…' + $val.Substring($val.Length-4) } else { '***' }
      $snippet = $lineText.Replace($val, "[REDACTED:$($rule.Name):$redacted]")

      $Findings.Add([pscustomobject]@{
        Path     = $file.FullName.Substring($Root.Length+1)
        Line     = $lineNumber
        Rule     = $rule.Name
        Snippet  = $snippet.Trim()
      })
    }
  }
}

if ($Findings.Count -gt 0) {
  $Findings | Sort-Object Path,Line,Rule | Tee-Object -Variable Sorted | Format-Table -AutoSize
  $Sorted | Export-Csv -NoTypeInformation -Encoding UTF8 $RegexCsv
  $Sorted | Out-File -Encoding UTF8 $RegexTxt
  Write-Host "`nRegex findings saved to:`n  $RegexCsv`n  $RegexTxt" -ForegroundColor Yellow
} else {
  Write-Host "No regex findings in working tree." -ForegroundColor Green
}

$HasDocker = Test-Docker
if ($HasDocker) {
  Write-Host "`n== Docker detected: running Gitleaks on working tree ==" -ForegroundColor Cyan
  $GlWork = Join-Path $OutputDir 'gitleaks-working.json'
  New-CleanDir $OutputDir
  try {
    # Пишем прямо в маунтируемый путь /repo/tools/reports/gitleaks-working.json
    docker run --rm -v "${Root}:/repo" zricethezav/gitleaks:latest `
      detect -s /repo --no-banner --redact --report-format json `
      --report-path /repo/tools/reports/gitleaks-working.json | Out-Null
    if (Test-Path $GlWork) { Write-Host "  gitleaks (working) report: $GlWork" }
  } catch { Write-Warning "Gitleaks (working) failed: $_" }

  if (-not $NoHistory) {
    Write-Host "== Gitleaks (history) + TruffleHog (git) ==" -ForegroundColor Cyan
    $mirror = Join-Path $Root '.mirror.git'
    if (Test-Path $mirror) { Remove-Item -Recurse -Force $mirror }
    git clone --mirror . $mirror | Out-Null

    $GlHist = Join-Path $mirror 'gitleaks-history.json'
    try {
      docker run --rm -v "${mirror}:/repo" zricethezav/gitleaks:latest `
        detect -s /repo --no-banner --redact --report-format json `
        --report-path /repo/gitleaks-history.json | Out-Null
      if (Test-Path $GlHist) { Write-Host "  gitleaks (history) report: $GlHist" }
    } catch { Write-Warning "Gitleaks (history) failed: $_" }

    $ThGit = Join-Path $mirror 'trufflehog-git.json'
    try {
      docker run --rm -v "${mirror}:/repo" trufflesecurity/trufflehog:latest `
        git file:///repo --only-verified --json > $ThGit
      if (Test-Path $ThGit) { Write-Host "  trufflehog (git) report: $ThGit" }
    } catch { Write-Warning "TruffleHog (git) failed: $_" }
  }
} else {
  Write-Host "`nDocker not available. Skipping Gitleaks/TruffleHog." -ForegroundColor DarkYellow
  Write-Host "Tip: install native gitleaks: 'scoop install gitleaks' and run: gitleaks detect -s . --no-banner --redact"
}

Write-Host "`n== Summary ==" -ForegroundColor Cyan
Write-Host ("Regex findings: {0}" -f $Findings.Count)
if ($HasDocker) {
  if (Test-Path $GlWork) { Write-Host "Gitleaks (working): $GlWork" }
  if (-not $NoHistory) {
    if (Test-Path $GlHist) { Write-Host "Gitleaks (history): $GlHist" }
    if (Test-Path $ThGit)  { Write-Host "TruffleHog (git):  $ThGit" }
  }
}

if ($Findings.Count -gt 0) { exit 2 } else { exit 0 }
