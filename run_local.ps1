$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
$dockerExe = if ($dockerCommand) { $dockerCommand.Source } else { 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' }

if (-not (Test-Path -LiteralPath $dockerExe)) {
    [Console]::Error.WriteLine('Docker Desktop CLI was not found. Install or repair Docker Desktop, then try again.')
    exit 1
}

if (-not (Test-Path -LiteralPath '.env')) {
    [Console]::Error.WriteLine('Missing .env. Copy .env.example to .env and configure the required secrets and OPENAI_API_KEY first.')
    exit 1
}

$envValues = @{}
Get-Content -LiteralPath '.env' | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
        $parts = $line.Split('=', 2)
        $envValues[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
}

$required = @('API_KEY', 'OPS_API_KEY', 'CI_ENCRYPTION_KEY', 'MYSQL_ROOT_PASSWORD', 'DB_PASSWORD', 'READONLY_DB_PASSWORD')
$provider = if ($envValues.ContainsKey('LLM_PROVIDER')) { $envValues['LLM_PROVIDER'].ToLowerInvariant() } else { 'openai' }
if ($provider -eq 'openai') {
    $required += 'OPENAI_API_KEY'
} elseif ($provider -eq 'ollama') {
    if (-not $envValues.ContainsKey('OLLAMA_BASE_URL')) {
        $envValues['OLLAMA_BASE_URL'] = 'http://host.docker.internal:11434'
    }
} else {
    [Console]::Error.WriteLine('LLM_PROVIDER must be set to openai or ollama.')
    exit 1
}
$missing = @($required | Where-Object { -not $envValues.ContainsKey($_) -or [string]::IsNullOrWhiteSpace($envValues[$_]) -or $envValues[$_] -match 'CHANGE_ME|YOUR_|REPLACE_ME' })
$priceKeys = if ($provider -eq 'openai') { @('LLM_INPUT_USD_PER_1M_TOKENS', 'LLM_OUTPUT_USD_PER_1M_TOKENS') } else { @() }
foreach ($name in $priceKeys) {
    $price = 0.0
    $validPrice = $envValues.ContainsKey($name) -and [double]::TryParse(
        $envValues[$name],
        [Globalization.NumberStyles]::Float,
        [Globalization.CultureInfo]::InvariantCulture,
        [ref]$price
    ) -and -not [double]::IsNaN($price) -and -not [double]::IsInfinity($price) -and $price -ge 0
    if (-not $validPrice) { $missing += $name }
}
if ($missing.Count -gt 0) {
    [Console]::Error.WriteLine("Configure these values in .env before starting: " + (($missing | Select-Object -Unique) -join ', '))
    exit 1
}

Write-Host 'Checking Docker Engine...' -ForegroundColor Cyan
& $dockerExe info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine('Docker Engine is not running. Open Docker Desktop and wait for Engine running. If it remains starting, restart Windows and check WSL status.')
    exit 1
}

Write-Host 'Starting MySQL, the API, and the CodeIgniter portal...' -ForegroundColor Cyan
& $dockerExe compose up --build
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine('Project Atlas did not start. Review the Docker Compose output above.')
    exit $LASTEXITCODE
}
