$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/4] Compile check" -ForegroundColor Cyan
python -m compileall -q cetapp main.py tools

Write-Host "[2/4] Unit tests" -ForegroundColor Cyan
python -m unittest discover -s tests

Write-Host "[3/4] Clean output" -ForegroundColor Cyan
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build\CET-Glass-Lab") { Remove-Item "build\CET-Glass-Lab" -Recurse -Force }

Write-Host "[4/4] Package Windows executable" -ForegroundColor Cyan
flet pack main.py `
    --name "CET-Glass-Lab" `
    --product-name "CET Glass Lab" `
    --file-description "大学英语四六级全真模考系统" `
    --product-version "1.0.0" `
    --file-version "1.0.0.0" `
    --company-name "CET Glass Lab" `
    --copyright "Copyright (c) 2026 CET Glass Lab" `
    --icon "assets/app.ico" `
    --add-data "assets;assets" `
    --hidden-import "cetapp.question_data" `
    --hidden-import "cetapp.paperlib" `
    --hidden-import "cetapp.pdf_import" `
    --hidden-import "cetapp.views.paper_exam" `
    --hidden-import "cetapp.views.wordbook" `
    --hidden-import "cetapp.views.import_paper" `
    --hidden-import "flet_audio" `
    --hidden-import "pypdf" `
    --hidden-import "PIL" `
    --hidden-import "cetapp.exam_service" `
    --hidden-import "cetapp.views.dashboard" `
    --hidden-import "cetapp.views.exam" `
    --hidden-import "cetapp.views.practice" `
    --hidden-import "cetapp.views.wrongbook" `
    --hidden-import "cetapp.views.history" `
    --hidden-import "cetapp.views.result" `
    --hidden-import "cetapp.views.qcomponents" `
    --distpath "dist" `
    -y

if (-not (Test-Path "dist\CET-Glass-Lab.exe")) {
    throw "Packaging failed: dist\CET-Glass-Lab.exe not found"
}

$size = [math]::Round((Get-Item "dist\CET-Glass-Lab.exe").Length / 1MB, 1)
Write-Host "Done: dist\CET-Glass-Lab.exe ($($size) MB)" -ForegroundColor Green
