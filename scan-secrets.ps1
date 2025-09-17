# scan-secrets.ps1 v5
[CmdletBinding()]
param(
  [string]$Path = ".",
  [int]$MaxFileSizeKB = 1024,
  [string]$OutFile = "",
  [switch]$Quiet,
  [switch]$Staged,              # git diff --cached
  [switch]$GitTracked,          # git ls-files
  [switch]$FailOnMedium,        # падать на medium тоже
  [switch]$NoRedact,            # показать полные совпадения (НЕ ИСП. в CI!)
  [int]$MaxPerFile = 50,        # лимит находок на файл (защита от спама)
  [int]$MaxInfoPerFile = 10,    # лимит info-энтропии на файл
  [string]$AllowFile = ".secrets-allow",
  [string[]]$ExtraExcludeRegex = @(), # дополнительные regex исключения путей
  [string[]]$IncludeRegex = @()       # сканировать только пути, совпадающие с любым из этих regex (опц.)
)

$ErrorActionPreference = 'Stop'

trap {
  if ($OutFile) { "[]" | Set-Content -LiteralPath $OutFile -Encoding UTF8 -ErrorAction SilentlyContinue }
  Write-Error $_
  exit 1
}

# ========= helpers =========
function Test-InGitRepo {
  try { $null = git rev-parse --is-inside-work-tree 2>$null; return $LASTEXITCODE -eq 0 } catch { return $false }
}

function Test-IsBinaryFile {
  param([string]$File)
  $binaryExt = @(
    '.png','.jpg','.jpeg','.gif','.webp','.ico','.pdf','.zip','.7z','.gz','.tar','.tgz','.rar',
    '.exe','.dll','.pdb','.so','.dylib','.bin','.woff','.woff2','.ttf','.eot'
  )
  try {
    $ext = [System.IO.Path]::GetExtension($File)
    if ($binaryExt -contains $ext.ToLower()) { return $true }
    $fs = [System.IO.File]::Open($File,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,[System.IO.FileShare]::ReadWrite)
    try {
      $buf = New-Object byte[] 1024
      $read = $fs.Read($buf,0,$buf.Length)
      for($i=0;$i -lt $read;$i++){ if($buf[$i] -eq 0){ return $true } }
    } finally { $fs.Dispose() }
  } catch { return $true }
  return $false
}

function Get-ShannonEntropy {
  param([string]$s)
  if([string]::IsNullOrEmpty($s)){ return 0.0 }
  $len = $s.Length
  $freq = @{}
  foreach($ch in $s.ToCharArray()){ if($freq.ContainsKey($ch)){ $freq[$ch]++ } else { $freq[$ch]=1 } }
  $entropy = 0.0
  foreach($kv in $freq.GetEnumerator()){
    $p = [double]$kv.Value / [double]$len
    $entropy += - $p * [Math]::Log($p,2)
  }
  [Math]::Round($entropy,3)
}

function Redact([string]$value){
  if ($NoRedact) { return $value }
  if ([string]::IsNullOrEmpty($value)) { return '<redacted>' }
  if ($value.Length -le 12) { return '<redacted>' }
  return ($value.Substring(0,6) + '…' + $value.Substring($value.Length-4))
}

function ShortLine([string]$s, [int]$max=160){
  $t = ($s.Trim() -replace '\s{2,}',' ')
  if ($t.Length -gt $max) { return $t.Substring(0,$max-1) + '…' }
  return $t
}

# ========= path filters =========
$excludeDirRegex = [regex]::new(
  '[/\\]\.(git|hg)|' +
  '[/\\]node_modules[/\\]|' +
  '[/\\](?:\.venv|venv)[/\\]|' +
  '[/\\]__pycache__[/\\]|' +
  '[/\\](?:dist|build)[/\\]|' +
  '[/\\]\.idea[/\\]|' +
  '[/\\]\.vscode[/\\]|' +
  '[/\\]vendor[/\\]|' +
  '[/\\](?:diag_bundle|tools[/\\]reports)[/\\]|' +
  '[/\\]\.mirror\.git[/\\]',
  'IgnoreCase'
)
$excludeFileRegex = [regex]::new(
  '(?i)(?:^|[/\\])(?:composer\.lock|package-lock\.json|yarn\.lock|pnpm-lock\.yaml)$'
)

# ========= allow-list parsing =========
# Поддерживаем формы:
#   path:<regex>     — игнорировать файлы по пути
#   rule:<NAME>      — игнорировать правило целиком
#   text:<regex>     — игнорировать совпадения по тексту/матчу
#   glob:<pattern>   — путь по glob (*, ?, **)
#   <regex>          — как text: <regex>
$allowRules = New-Object System.Collections.Generic.HashSet[string]
$allowPath = New-Object System.Collections.Generic.List[regex]
$allowText = New-Object System.Collections.Generic.List[regex]

function GlobToRegex([string]$g){
  $e = [regex]::Escape($g) -replace '\\\*\\\*','__GLOBSTAR__'
  $e = $e -replace '\\\*','[^/\\]*' -replace '\\\?','.'
  $e = $e -replace '__GLOBSTAR__','.*'
  return '^(?:' + $e + ')$'
}

if (Test-Path $AllowFile) {
  foreach($raw in (Get-Content $AllowFile | Where-Object { $_ -and $_ -notmatch '^\s*#' })){
    $line = $raw.Trim()
    if ($line -match '^(?i)path:(.+)$'){ $allowPath.Add([regex]::new($Matches[1],'IgnoreCase')) ; continue }
    if ($line -match '^(?i)rule:(.+)$'){ [void]$allowRules.Add($Matches[1].Trim()) ; continue }
    if ($line -match '^(?i)text:(.+)$'){ $allowText.Add([regex]::new($Matches[1])) ; continue }
    if ($line -match '^(?i)glob:(.+)$'){ $allowPath.Add([regex]::new((GlobToRegex $Matches[1]),'IgnoreCase')) ; continue }
    # по умолчанию — text
    $allowText.Add([regex]::new($line))
  }
}

function IsAllowed($file, $ruleName, $text){
  if ($allowRules.Contains($ruleName)) { return $true }
  foreach($rx in $allowPath){ if ($rx.IsMatch($file)) { return $true } }
  foreach($rx in $allowText){ if ($rx.IsMatch($text)) { return $true } }
  return $false
}

# ========= choose targets =========
function Get-TargetFiles {
  $inGit = Test-InGitRepo
  if ($Staged -and -not $inGit) { Write-Verbose "Not in a git repo; ignoring -Staged"; $Staged = $false }
  if ($GitTracked -and -not $inGit) { Write-Verbose "Not in a git repo; ignoring -GitTracked"; $GitTracked = $false }

  if ($Staged) {
    $root = (git rev-parse --show-toplevel).Trim()
    $names = (git diff --cached --name-only) -split "`n" | Where-Object { $_ }
    $files = $names | ForEach-Object { Join-Path -Path $root -ChildPath $_ }
  } elseif ($GitTracked) {
    $root = (git rev-parse --show-toplevel).Trim()
    $names = (git ls-files) -split "`n" | Where-Object { $_ }
    $files = $names | ForEach-Object { Join-Path -Path $root -ChildPath $_ }
  } else {
    $files = Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
  }

  $files | Where-Object {
    $f = $_
    if (-not (Test-Path $f)) { return $false }
    if ($excludeDirRegex.IsMatch($f)) { return $false }
    if ($excludeFileRegex.IsMatch($f)) { return $false }
    foreach($rx in $ExtraExcludeRegex){ if ($f -match $rx){ return $false } }
    if ($IncludeRegex.Count -gt 0) {
      $ok = $false; foreach($irx in $IncludeRegex){ if ($f -match $irx){ $ok = $true; break } }
      if (-not $ok) { return $false }
    }
    # не сканируем allow-файл
    if ([System.IO.Path]::GetFileName($f) -eq [System.IO.Path]::GetFileName($AllowFile)) { return $false }
    ((Get-Item $f).Length -le ($MaxFileSizeKB*1KB)) -and -not (Test-IsBinaryFile -File $f)
  }
}

# ========= detection rules =========
$rules = @(
  @{ Name='PrivateKeyBlock';     Severity='high';   Pattern='-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP|PRIVATE) KEY-----' },
  @{ Name='AWS_AccessKeyId';     Severity='high';   Pattern='\bAKIA[0-9A-Z]{16}\b' },
  @{ Name='AWS_SecretAccessKey'; Severity='high';   Pattern='(?i)\b(?:(?:aws)?_?secret(?:_access)?_?key|aws_secret_access_key)\b.{0,50}?([A-Za-z0-9\/+=]{40})' },
  @{ Name='GitHub_PAT';          Severity='high';   Pattern='\bgh[pousr]_[A-Za-z0-9]{20,80}\b' },
  @{ Name='GitLab_PAT';          Severity='high';   Pattern='\bglpat-[A-Za-z0-9\-_]{20,}\b' },
  @{ Name='Telegram_BotToken';   Severity='high';   Pattern='\b\d{8,12}:[A-Za-z0-9_-]{30,60}\b' },
  @{ Name='Slack_Token';         Severity='high';   Pattern='\bxox(?:a|b|p|r|s)-[A-Za-z0-9-]{10,48}\b' },
  @{ Name='Google_API_Key';      Severity='high';   Pattern='\bAIza[0-9A-Za-z\-_]{35}\b' },
  @{ Name='Stripe_SK';           Severity='high';   Pattern='\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b' },
  @{ Name='OpenAI_SK';           Severity='high';   Pattern='\bsk-[A-Za-z0-9]{20,}\b' },
  @{ Name='CF_Tunnel_Token';     Severity='high';   Pattern='CF_TUNNEL_TOKEN\s*=\s*eyJ[A-Za-z0-9_\-]*\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+' },

  # логин:пароль@ в URL; игнорирует ${...} и \${...}
  @{ Name='URL_Credentials';     Severity='high';   Pattern='://(?!\\?\$\{)[^/\s:@]{1,128}:(?!\\?\$\{)[^/\s@]{6,128}@' },

  @{ Name='JWT';                 Severity='medium'; Pattern='\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b' },
  @{ Name='Generic_PasswordAssign'; Severity='medium'; Pattern='(?im)^\s*(password|passwd|pwd|secret(_key)?|token|apikey|api_key|access_key|client_secret)\s*[:=]\s*[^#\r\n]+' },
  @{ Name='Env_Secrets_File';    Severity='medium'; Pattern='(?im)^\s*(?:SECRET|SECRET_KEY|JWT_SECRET|DB_PASS(?:WORD)?|POSTGRES_PASSWORD|REDIS_PASSWORD|TELEGRAM_BOT_TOKEN|BOT_TOKEN)\s*=\s*.+$' }
)

$genericTokenFinders = @(
  @{ Name='Base64_Long'; Severity='info'; Pattern='\b[A-Za-z0-9+\/]{32,}={0,2}\b'; EntropyMin=3.6 },
  @{ Name='Hex_Long';    Severity='info'; Pattern='\b[0-9a-fA-F]{32,}\b';          EntropyMin=3.6 }
)

# ========= scan =========
$targets = Get-TargetFiles
$findings = New-Object System.Collections.Generic.List[object]

foreach($file in $targets){
  $content = $null
  try {
    try { $content = Get-Content -LiteralPath $file -Raw -Encoding UTF8 -ErrorAction Stop }
    catch {
      $bytes = [System.IO.File]::ReadAllBytes($file)
      $content = [Text.Encoding]::UTF8.GetString($bytes)
    }
  } catch { continue }

  if ($null -eq $content) { $content = "" }
  $content = $content -replace "`r`n","`n"

  $addedForFile = 0
  $infoForFile  = 0

  foreach($rule in $rules){
    if ($addedForFile -ge $MaxPerFile) { break }
    try {
      $matches = [regex]::Matches($content, $rule.Pattern)
      foreach($m in $matches){
        if ($addedForFile -ge $MaxPerFile) { break }

        # allow?
        if (IsAllowed -file (Resolve-Path $file).Path -ruleName $rule.Name -text $m.Value) { continue }

        $prefix  = if ($m.Index -gt 0) { $content.Substring(0,$m.Index) } else { "" }
        $lineNum = [Math]::Max(1, ($prefix -split "`n").Count)
        $lines   = $content -split "`n"
        $lineTxt = if ($lineNum -le $lines.Count) { $lines[$lineNum-1] } else { "" }

        $sev = $rule.Severity
        if ($sev -eq 'info') {
          if ($infoForFile -ge $MaxInfoPerFile) { continue }
          $infoForFile++
        }

        $findings.Add([pscustomobject]@{
          File=(Resolve-Path $file).Path
          Line=$lineNum
          Rule=$rule.Name
          Severity=$sev
          Snippet=(ShortLine $lineTxt)
          Match=(Redact $m.Value)
        })
        $addedForFile++
      }
    } catch { }
  }

  if ($addedForFile -ge $MaxPerFile) {
    $findings.Add([pscustomobject]@{
      File=(Resolve-Path $file).Path
      Line=0
      Rule='Scanner'
      Severity='info'
      Snippet="Truncated output: reached MaxPerFile=$MaxPerFile"
      Match='<omitted>'
    })
  }

  foreach($g in $genericTokenFinders){
    if ($infoForFile -ge $MaxInfoPerFile) { break }
    try {
      $matches = [regex]::Matches($content, $g.Pattern)
      foreach($m in $matches){
        if ($infoForFile -ge $MaxInfoPerFile) { break }
        $token = $m.Value
        if ($token.Length -lt 48) { continue }
        $H = Get-ShannonEntropy $token
        if ($H -ge $g.EntropyMin){
          $prefix  = if ($m.Index -gt 0) { $content.Substring(0,$m.Index) } else { "" }
          $lineNum = [Math]::Max(1, ($prefix -split "`n").Count)
          $lineTxt = ($content -split "`n")[$lineNum-1]
          if (-not (IsAllowed -file (Resolve-Path $file).Path -ruleName $g.Name -text $token)) {
            $findings.Add([pscustomobject]@{
              File=(Resolve-Path $file).Path
              Line=$lineNum
              Rule=$g.Name
              Severity='info'
              Entropy=$H
              Match=(Redact $token)
              Snippet=(ShortLine $lineTxt)
            })
            $infoForFile++
          }
        }
      }
    } catch { }
  }
}

# ========= report & exit code =========
$high = $findings | Where-Object { $_.Severity -eq 'high' }
$med  = $findings | Where-Object { $_.Severity -eq 'medium' }
$inf  = $findings | Where-Object { $_.Severity -eq 'info' }

if (-not $Quiet){
  Write-Host "== Secret scan report ==" -ForegroundColor Cyan
  Write-Host ("High:   {0}" -f ($high | Measure-Object).Count) -ForegroundColor Red
  Write-Host ("Medium: {0}" -f ($med  | Measure-Object).Count) -ForegroundColor Yellow
  Write-Host ("Info:   {0}" -f ($inf  | Measure-Object).Count) -ForegroundColor Gray
  if($findings.Count){
    Write-Host ""
    $findings | Sort-Object Severity,File,Line |
      Format-Table Severity,Rule,File,Line,Snippet -AutoSize | Out-Host
  }
}

if ($OutFile){
  $findings | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutFile -Encoding UTF8
  if(-not $Quiet){ Write-Host "Saved report: $OutFile" -ForegroundColor DarkCyan }
}

if ($FailOnMedium) {
  if ((($high | Measure-Object).Count + ($med | Measure-Object).Count) -gt 0){ exit 2 } else { exit 0 }
} else {
  if (($high | Measure-Object).Count -gt 0){ exit 2 } else { exit 0 }
}
