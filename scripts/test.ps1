$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"; & .\.venv\Scripts\python.exe -m pytest -q
Set-Location "..\frontend"; npx tsc --noEmit; npm run build
