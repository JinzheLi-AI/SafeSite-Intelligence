$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../backend')
$env:SAFESITE_AI_PROVIDER='mock'
$env:SAFESITE_VISION_PROVIDER='mock'
$env:SAFESITE_REINSPECTION_PROVIDER='mock'
$env:SAFESITE_VISION_PROMPT_VERSION='vision-v1'
$env:SAFESITE_ANALYST_PROVIDER='deterministic'
$env:SAFESITE_EMBEDDING_PROVIDER='fastembed'
$env:DATABASE_URL='sqlite:///./data/day1-demo.db'
$env:UPLOAD_DIR='./data/day1-uploads'
$env:CORS_ORIGINS='["http://127.0.0.1:3002"]'
$env:AUTO_SEED='true'
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
