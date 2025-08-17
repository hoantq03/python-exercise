# Build script for Product Management App
# Author: Generated for user
# Date: $(Get-Date)

Write-Host "=== Product Management App Build Script ===" -ForegroundColor Green
Write-Host ""

# --- 1) Cấu hình ứng dụng ---
$MAIN_SCRIPT = "main.py"
$APP_ICON    = "app/assets/icons/app_icon.ico"
$DATA_DIR    = "app/data" # Thư mục chứa dữ liệu nguồn
$APP_NAME    = "ProductManagementApp"

Write-Host "App Name: $APP_NAME" -ForegroundColor Cyan
Write-Host "Main Script: $MAIN_SCRIPT" -ForegroundColor Cyan
Write-Host "Data Directory: $DATA_DIR" -ForegroundColor Cyan
Write-Host ""

# --- 2) Kiểm tra các file và thư mục cần thiết ---
Write-Host "Checking required files and directories..." -ForegroundColor Yellow
$requiredPaths = @(
    $MAIN_SCRIPT,
    $APP_ICON,
    "requirements.txt",
    $DATA_DIR # Chỉ cần kiểm tra thư mục data là đủ
)

$missingPaths = @()
foreach ($path in $requiredPaths) {
    if (!(Test-Path $path)) {
        $missingPaths += $path
        Write-Host "❌ Missing: $path" -ForegroundColor Red
    } else {
        Write-Host "✅ Found: $path" -ForegroundColor Green
    }
}

if ($missingPaths.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Build failed! Missing required files/directories." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All required components found!" -ForegroundColor Green
Write-Host ""

# --- 3) Cài đặt các thư viện ---
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Requirements installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install requirements!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# --- 4) Cấu hình tham số PyInstaller ---
Write-Host "--- BUILDING IN ONE-DIR DEBUG MODE ---" -ForegroundColor Magenta
$pyinstallerArgs = @(
    "--name", $APP_NAME,
    "--onefile",
    "--windowed",
    "--add-data", "$DATA_DIR;data",
    "--icon", $APP_ICON,
    $MAIN_SCRIPT
)


# --- 5) Dọn dẹp các bản build cũ ---
Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
$dirsToClean = @("build", "dist")
foreach ($dir in $dirsToClean) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Host "✅ Cleaned directory: $dir" -ForegroundColor Green
    }
}
if (Test-Path "$APP_NAME.spec") {
    Remove-Item -Force "$APP_NAME.spec"
    Write-Host "✅ Cleaned spec file: $APP_NAME.spec" -ForegroundColor Green
}

Write-Host ""

# --- 6) Chạy PyInstaller ---
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
Write-Host "Command: pyinstaller $($pyinstallerArgs -join ' ')" -ForegroundColor Cyan
Write-Host ""

try {
    # Chạy PyInstaller
    & pyinstaller @pyinstallerArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
        Write-Host "📁 Executable location: dist\$APP_NAME.exe" -ForegroundColor Cyan

        # Kiểm tra file exe và báo cáo kích thước
        if (Test-Path "dist\$APP_NAME.exe") {
            $exeSize = (Get-Item "dist\$APP_NAME.exe").Length / 1MB
            Write-Host "📊 File size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
        }
    } else {
        Write-Host ""
        Write-Host "❌ Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Build failed with a script error:" -ForegroundColor Red
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
