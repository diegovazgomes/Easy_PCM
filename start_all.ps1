# start_all.ps1
# Inicia: Uvicorn + Ngrok + configura Webhook do Telegram automaticamente (corrigido para caminhos com espaço)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-DotEnvValue([string]$key) {
    $envPath = Join-Path $PSScriptRoot ".env"
    if (-not (Test-Path $envPath)) { throw "Arquivo .env não encontrado em: $envPath" }

    foreach ($line in Get-Content $envPath) {
        $trim = $line.Trim()
        if ($trim -eq "" -or $trim.StartsWith("#")) { continue }
        $parts = $trim.Split("=", 2)
        if ($parts.Count -ne 2) { continue }
        if ($parts[0].Trim() -eq $key) { return $parts[1].Trim() }
    }
    return $null
}

$TELEGRAM_BOT_TOKEN = Get-DotEnvValue "TELEGRAM_BOT_TOKEN"
if (-not $TELEGRAM_BOT_TOKEN) { throw "TELEGRAM_BOT_TOKEN não encontrado no .env" }

$port = 8000

# Ativar venv (para o script atual)
$activatePath = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $activatePath)) { throw "Ambiente virtual não encontrado. Crie com: python -m venv .venv" }
. $activatePath

# Iniciar Uvicorn em nova janela (CORRIGIDO: caminho com espaço)
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "& { Set-Location -LiteralPath '$PSScriptRoot'; . '.\.venv\Scripts\Activate.ps1'; python -m uvicorn app:app --reload --port $port }"
) | Out-Null

# Iniciar Ngrok em nova janela
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "ngrok http $port"
) | Out-Null

Write-Host "Aguardando ngrok iniciar..."
$publicUrl = $null

for ($i = 0; $i -lt 60; $i++) {
    try {
        $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
        $httpsTunnel = $tunnels.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1
        if ($httpsTunnel) { $publicUrl = $httpsTunnel.public_url; break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $publicUrl) { throw "Não consegui obter a URL do ngrok (4040). Verifique se o ngrok abriu corretamente." }

Write-Host "URL pública do ngrok: $publicUrl"

Write-Host "Aguardando servidor FastAPI ficar pronto..."
$healthOk = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
        if ($h.ok -eq $true) { $healthOk = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $healthOk) {
    throw "Servidor não respondeu /health. Verifique o terminal do uvicorn para erros."
}

$webhookUrl = "$publicUrl/telegram/webhook"
$setWebhookEndpoint = "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook"

Write-Host "Configurando webhook no Telegram: $webhookUrl"
$setOk = $false

for ($i = 0; $i -lt 10; $i++) {
    try {
        $resp = Invoke-RestMethod -Method Post -Uri $setWebhookEndpoint -Body @{ url = $webhookUrl }
        if ($resp.ok -eq $true) { $setOk = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $setOk) { throw "Falha ao configurar webhook no Telegram após retries." }

Write-Host "Webhook configurado com sucesso."
Write-Host "Tudo iniciado. Servidor + ngrok rodando e webhook atualizado."
