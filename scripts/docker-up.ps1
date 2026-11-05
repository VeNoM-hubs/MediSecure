# Build and start the production-oriented Compose stack (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
  Write-Error "Missing .env — copy .env.example to .env and set secrets first."
}

docker compose -f docker-compose.yml up --build -d @args
$port = if ($env:FRONTEND_HOST_PORT) { $env:FRONTEND_HOST_PORT } else { "8080" }
Write-Host "MediSecure started. UI: http://localhost:$port"
