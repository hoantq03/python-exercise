#!/bin/bash

# Build script for Product Management App
# Author: Generated for user
# Date: $(date)

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
DARK_CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Product Management App Build Script ===${NC}"
echo ""

# 1) App config
MAIN_SCRIPT="main.py"
APP_ICON="app/assets/icons/app_icon.ico"
DATA_DIR="app/data"
APP_NAME="ProductManagementApp"

echo -e "${CYAN}App Name: $APP_NAME${NC}"
echo -e "${CYAN}Main Script: $MAIN_SCRIPT${NC}"
echo -e "${CYAN}Icon: $APP_ICON${NC}"
echo ""

# 2) Check if required files exist
echo -e "${YELLOW}Checking required files...${NC}"
required_files=(
    "$MAIN_SCRIPT"
    "$APP_ICON"
    "requirements.txt"
    "$DATA_DIR/products.json"
    "$DATA_DIR/carts.json"
    "$DATA_DIR/categories.json"
    "$DATA_DIR/customers.json"
    "$DATA_DIR/orders.json"
    "$DATA_DIR/users.json"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
        echo -e "${RED}❌ Missing: $file${NC}"
    else
        echo -e "${GREEN}✅ Found: $file${NC}"
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo ""
    echo -e "${RED}❌ Build failed! Missing required files.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All required files found!${NC}"
echo ""

# 3) Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
if pip install -r requirements.txt; then
    echo -e "${GREEN}✅ Requirements installed successfully!${NC}"
else
    echo -e "${RED}❌ Failed to install requirements!${NC}"
    exit 1
fi

echo ""

# 4) PyInstaller args
pyinstaller_args=(
    "--name" "$APP_NAME"
    "--onefile"
    "--windowed"
    "--add-data" "$DATA_DIR/products.json:."
    "--add-data" "$DATA_DIR/carts.json:."
    "--add-data" "$DATA_DIR/categories.json:."
    "--add-data" "$DATA_DIR/customers.json:."
    "--add-data" "$DATA_DIR/orders.json:."
    "--add-data" "$DATA_DIR/users.json:."
    "--icon" "$APP_ICON"
    "$MAIN_SCRIPT"
)

# 5) Clean previous build
echo -e "${YELLOW}Cleaning previous build...${NC}"
if [[ -d "build" ]]; then
    rm -rf "build"
    echo -e "${GREEN}✅ Cleaned build directory${NC}"
fi
if [[ -d "dist" ]]; then
    rm -rf "dist"
    echo -e "${GREEN}✅ Cleaned dist directory${NC}"
fi
if [[ -f "$APP_NAME.spec" ]]; then
    rm -f "$APP_NAME.spec"
    echo -e "${GREEN}✅ Cleaned spec file${NC}"
fi

echo ""

# 6) Run PyInstaller
echo -e "${YELLOW}Building executable with PyInstaller...${NC}"
echo -e "${CYAN}Command: pyinstaller ${pyinstaller_args[*]}${NC}"
echo ""

if pyinstaller "${pyinstaller_args[@]}"; then
    echo ""
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    echo -e "${CYAN}📁 Executable location: dist/$APP_NAME${NC}"

    # Check if executable was created
    if [[ -f "dist/$APP_NAME" ]]; then
        exe_size=$(du -m "dist/$APP_NAME" | cut -f1)
        echo -e "${CYAN}📊 File size: $exe_size MB${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Build failed with exit code: $?${NC}"
    exit 1
fi

echo ""

# 7) Display ASCII Banner
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${MAGENTA}║                                  🎯 BUILD SUCCESS 🎯                                        ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${GREEN}║  ██████  ██    ██ ██ ██      ██████       ██████  ██   ██                                  ║${NC}"
echo -e "${GREEN}║  ██   ██ ██    ██ ██ ██      ██   ██     ██    ██ ██  ██                                   ║${NC}"
echo -e "${GREEN}║  ██████  ██    ██ ██ ██      ██   ██     ██    ██ █████                                    ║${NC}"
echo -e "${GREEN}║  ██   ██ ██    ██ ██ ██      ██   ██     ██    ██ ██  ██                                   ║${NC}"
echo -e "${GREEN}║  ██████   ██████  ██ ███████ ██████       ██████  ██   ██                                  ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${YELLOW}║          ██████  ██████  ███    ███ ██████  ██      ███████                                ║${NC}"
echo -e "${YELLOW}║         ██      ██    ██ ████  ████ ██   ██ ██      ██                                     ║${NC}"
echo -e "${YELLOW}║         ██      ██    ██ ██ ████ ██ ██████  ██      █████                                  ║${NC}"
echo -e "${YELLOW}║         ██      ██    ██ ██  ██  ██ ██      ██      ██                                     ║${NC}"
echo -e "${YELLOW}║          ██████  ██████  ██      ██ ██      ███████ ███████                                ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${DARK_CYAN}║    ╔══════════════════════════════════════════════════════════════════════════════════╗    ║${NC}"
echo -e "${DARK_CYAN}║    ║                              ✨ BUILT BY ✨                                      ║    ║${NC}"
echo -e "${DARK_CYAN}║    ╚══════════════════════════════════════════════════════════════════════════════════╝    ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${GREEN}║   ______                    ____                      __  __                               ║${NC}"
echo -e "${GREEN}║  /_  __/________ _____     / __ \\__  ______  _____   / / / /___  ____ _____                ║${NC}"
echo -e "${GREEN}║   / / / ___/ __ \`/ __ \\   / / / / / / / __ \\/ ___/  / /_/ / __ \\/ __ \`/ __ \\               ║${NC}"
echo -e "${GREEN}║  / / / /  / /_/ / / / /  / /_/ / /_/ / /_/ / /__   / __  / /_/ / /_/ / / / /               ║${NC}"
echo -e "${GREEN}║ /_/ /_/   \\__,_/_/ /_/   \\___\\_\\__,_/\\____/\\___/  /_/ /_/\\____/\\__,_/_/ /_/                ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${WHITE}║  ┌──────────────────────────────────────────────────────────────────────────────────────┐  ║${NC}"
echo -e "${WHITE}║  │                            📅 BUILD INFORMATION                                        │  ║${NC}"
echo -e "${WHITE}║  │                                                                                      │  ║${NC}"
echo -e "${WHITE}║  │    🗓️  Date: $(date '+%d/%m/%Y %H:%M:%S')                                            │  ║${NC}"
echo -e "${WHITE}║  │    📍 Location: Ho Chi Minh City, Vietnam                                           │  ║${NC}"
echo -e "${WHITE}║  │    💻 Platform: Linux/macOS Bash                                                    │  ║${NC}"
echo -e "${WHITE}║  │    🎯 Status: BUILD COMPLETED SUCCESSFULLY                                          │  ║${NC}"
echo -e "${WHITE}║  │                                                                                      │  ║${NC}"
echo -e "${WHITE}║  └──────────────────────────────────────────────────────────────────────────────────────┘  ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${MAGENTA}║                        ⭐ Thank you for using this build script! ⭐                        ║${NC}"
echo -e "${CYAN}║                                                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}                              🚀 Build completed successfully! 🚀                            ${NC}"
echo -e "${BLUE}                                 Ready to launch your application                            ${NC}"
echo ""
