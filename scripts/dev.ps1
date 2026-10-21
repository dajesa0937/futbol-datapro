# Arranca API (8000) y web (3000) en dos ventanas.
$root = Resolve-Path "$PSScriptRoot\.."
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; npm run dev"
Start-Process "http://localhost:3000"
