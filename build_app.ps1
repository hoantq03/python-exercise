# Build script for Product Management App
# Author: Generated for user
# Date: $(Get-Date)

Write-Host "=== Product Management App Build Script ===" -ForegroundColor Green
Write-Host ""

# 1) App config
$MAIN_SCRIPT = "main.py"
$APP_ICON    = "app/assets/icons/app_icon.ico"
$DATA_DIR    = "app/data"
$APP_NAME    = "ProductManagementApp"

Write-Host "App Name: $APP_NAME" -ForegroundColor Cyan
Write-Host "Main Script: $MAIN_SCRIPT" -ForegroundColor Cyan
Write-Host "Icon: $APP_ICON" -ForegroundColor Cyan
Write-Host ""

# 2) Check if required files exist
Write-Host "Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    $MAIN_SCRIPT,
    $APP_ICON,
    "requirements.txt",
    "$DATA_DIR/products.json",
    "$DATA_DIR/carts.json",
    "$DATA_DIR/categories.json",
    "$DATA_DIR/customers.json",
    "$DATA_DIR/orders.json",
    "$DATA_DIR/users.json"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $missingFiles += $file
        Write-Host "❌ Missing: $file" -ForegroundColor Red
    } else {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Build failed! Missing required files." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All required files found!" -ForegroundColor Green
Write-Host ""

# 3) Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Requirements installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install requirements!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# 4) PyInstaller args
$pyinstallerArgs = @(
    "--name", $APP_NAME,
    "--onefile",
    "--windowed",
    "--add-data", "$DATA_DIR/products.json;.",
    "--add-data", "$DATA_DIR/carts.json;.",
    "--add-data", "$DATA_DIR/categories.json;.",
    "--add-data", "$DATA_DIR/customers.json;.",
    "--add-data", "$DATA_DIR/orders.json;.",
    "--add-data", "$DATA_DIR/users.json;.",
    "--icon", $APP_ICON,
    $MAIN_SCRIPT
)

# 5) Clean previous build
Write-Host "Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "✅ Cleaned build directory" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "✅ Cleaned dist directory" -ForegroundColor Green
}
if (Test-Path "$APP_NAME.spec") {
    Remove-Item -Force "$APP_NAME.spec"
    Write-Host "✅ Cleaned spec file" -ForegroundColor Green
}

Write-Host ""

# 6) Run PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
Write-Host "Command: pyinstaller $($pyinstallerArgs -join ' ')" -ForegroundColor Cyan
Write-Host ""

try {
    & pyinstaller @pyinstallerArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
        Write-Host "📁 Executable location: dist/$APP_NAME.exe" -ForegroundColor Cyan

        # Check if executable was created
        if (Test-Path "dist/$APP_NAME.exe") {
            $exeSize = (Get-Item "dist/$APP_NAME.exe").Length / 1MB
            Write-Host "📊 File size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
        }
    } else {
        Write-Host ""
        Write-Host "❌ Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Build failed with error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║                                  🎯 BUILD SUCCESS 🎯                                        ║" -ForegroundColor Magenta
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║  ██████  ██    ██ ██ ██      ██████       ██████  ██   ██                                  ║" -ForegroundColor Green
Write-Host "║  ██   ██ ██    ██ ██ ██      ██   ██     ██    ██ ██  ██                                   ║" -ForegroundColor Green
Write-Host "║  ██████  ██    ██ ██ ██      ██   ██     ██    ██ █████                                    ║" -ForegroundColor Green
Write-Host "║  ██   ██ ██    ██ ██ ██      ██   ██     ██    ██ ██  ██                                   ║" -ForegroundColor Green
Write-Host "║  ██████   ██████  ██ ███████ ██████       ██████  ██   ██                                  ║" -ForegroundColor Green
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║          ██████  ██████  ███    ███ ██████  ██      ███████                                ║" -ForegroundColor Yellow
Write-Host "║         ██      ██    ██ ████  ████ ██   ██ ██      ██                                     ║" -ForegroundColor Yellow
Write-Host "║         ██      ██    ██ ██ ████ ██ ██████  ██      █████                                  ║" -ForegroundColor Yellow
Write-Host "║         ██      ██    ██ ██  ██  ██ ██      ██      ██                                     ║" -ForegroundColor Yellow
Write-Host "║          ██████  ██████  ██      ██ ██      ███████ ███████                                ║" -ForegroundColor Yellow
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║    ╔══════════════════════════════════════════════════════════════════════════════════╗    ║" -ForegroundColor DarkCyan
Write-Host "║    ║                              ✨ BUILT BY ✨                                      ║    ║" -ForegroundColor DarkCyan
Write-Host "║    ╚══════════════════════════════════════════════════════════════════════════════════╝    ║" -ForegroundColor DarkCyan
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║   ______                    ____                      __  __                               ║" -ForegroundColor Green
Write-Host "║  /_  __/________ _____     / __ \__  ______  _____   / / / /___  ____ _____                ║" -ForegroundColor Green
Write-Host "║   / / / ___/ __ `/ __ \   / / / / / / / __ \/ ___/  / /_/ / __ \/ __ `/ __ \               ║" -ForegroundColor Green
Write-Host "║  / / / /  / /_/ / / / /  / /_/ / /_/ / /_/ / /__   / __  / /_/ / /_/ / / / /               ║" -ForegroundColor Green
Write-Host "║ /_/ /_/   \__,_/_/ /_/   \___\_\__,_/\____/\___/  /_/ /_/\____/\__,_/_/ /_/                ║" -ForegroundColor Green
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║  ┌──────────────────────────────────────────────────────────────────────────────────────┐  ║" -ForegroundColor White
Write-Host "║  │                            📅 BUILD INFORMATION                                        │  ║" -ForegroundColor White
Write-Host "║  │                                                                                      │  ║" -ForegroundColor White
Write-Host "║  │    🗓️  Date: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')                                            │  ║" -ForegroundColor White
Write-Host "║  │    📍 Location: Ho Chi Minh City, Vietnam                                           │  ║" -ForegroundColor White
Write-Host "║  │    💻 Platform: Windows PowerShell                                                  │  ║" -ForegroundColor White
Write-Host "║  │    🎯 Status: BUILD COMPLETED SUCCESSFULLY                                          │  ║" -ForegroundColor White
Write-Host "║  │                                                                                      │  ║" -ForegroundColor White
Write-Host "║  └──────────────────────────────────────────────────────────────────────────────────────┘  ║" -ForegroundColor White
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "║                        ⭐ Thank you for using this build script! ⭐                        ║" -ForegroundColor Magenta
Write-Host "║                                                                                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "                              🚀 Build completed successfully! 🚀                            " -ForegroundColor Green
Write-Host "                                 Ready to launch your application                            " -ForegroundColor Blue
Write-Host ""
