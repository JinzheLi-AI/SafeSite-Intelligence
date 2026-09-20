param([switch]$Development)
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../frontend')
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8002/api/v1'
if ($Development) { npm.cmd run dev -- --port 3002 }
else { npm.cmd run start -- --port 3002 }
