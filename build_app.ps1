# build_app.ps1

# Tên file Python chính của ứng dụng
$MAIN_SCRIPT = "main.py"

# Tên file icon (phải là định dạng .ico cho Windows)
$APP_ICON = "app/assets/icons/app_icon.ico"

# Thư mục chứa các file JSON data
$DATA_DIR = "app/data"

# Tên ứng dụng (sẽ là tên của file .exe hoặc thư mục sau khi build)
$APP_NAME = "ProductManagementApp"

# --- Lệnh PyInstaller ---
Write-Host "Bắt đầu đóng gói ứng dụng '$APP_NAME' với PyInstaller..."

# Định nghĩa các arguments cho PyInstaller
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

# Chạy PyInstaller
# Sử dụng & để gọi một executable bên ngoài
& pyinstaller $pyinstallerArgs

# Kiểm tra kết quả
if ($LASTEXITCODE -eq 0) {
  Write-Host "✅ Đóng gói thành công! File thực thi có thể tìm thấy trong thư mục 'dist/'."
  Write-Host "Tên file: dist/$APP_NAME.exe"
} else {
  Write-Host "❌ Đóng gói thất bại. Vui lòng kiểm tra các thông báo lỗi bên trên."
}

Write-Host "Hoàn tất."
