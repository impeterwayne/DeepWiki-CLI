# DeepWiki CLI - 1-Command PowerShell Installer
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "         DeepWiki CLI - 1-Command Installer            " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python was not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://python.org or your package manager." -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] Installing DeepWiki CLI package and dependencies..." -ForegroundColor Green
python -m pip install -e .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Package installation failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/2] Installing Playwright Chromium browser..." -ForegroundColor Green
python -m playwright install chromium

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " SUCCESS! DeepWiki CLI is installed." -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run 'deepwiki' directly from anywhere:" -ForegroundColor White
Write-Host "  deepwiki https://github.com/microsoft/vscode" -ForegroundColor Yellow
Write-Host "  deepwiki microsoft/vscode -c 10" -ForegroundColor Yellow
Write-Host "  deepwiki --help" -ForegroundColor Yellow
Write-Host ""
