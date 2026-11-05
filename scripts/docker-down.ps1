# Stop containers without deleting the postgres_data volume (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

docker compose -f docker-compose.yml -f docker-compose.dev.yml down @args
Write-Host "Containers stopped. Volume medisecure_postgres_data was preserved (no -v)."
