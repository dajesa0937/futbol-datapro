# Instalación inicial en Windows 11 (PowerShell). Ejecutar desde la raíz del repositorio.
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Set-Location "..\frontend"
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm install
Write-Host "Listo. Ejecuta: .\scripts\dev.ps1"
