#!/bin/bash

# Tên file Python chính của ứng dụng
MAIN_SCRIPT="main.py"

# Tên file icon (phải là định dạng .ico cho Windows hoặc tương thích cho macOS)
APP_ICON="app/assets/icons/app_icon.ico"

# Thư mục chứa các file JSON data
DATA_DIR="app/data"

# Tên ứng dụng (sẽ là tên của file .exe hoặc thư mục sau khi build)
APP_NAME="ProductManagementApp"

# --- Lệnh PyInstaller ---
echo "Bắt đầu đóng gói ứng dụng '$APP_NAME' với PyInstaller..."

pyinstaller \
  --name "$APP_NAME" \
  --onefile \
  --windowed \
  --add-data "$DATA_DIR/products.json;." \
  --add-data "$DATA_DIR/carts.json;." \
  --add-data "$DATA_DIR/categories.json;." \
  --add-data "$DATA_DIR/customers.json;." \
  --add-data "$DATA_DIR/orders.json;." \
  --add-data "$DATA_DIR/users.json;." \
  --icon="$APP_ICON" \
  "$MAIN_SCRIPT"

# Kiểm tra kết quả
if [ $? -eq 0 ]; then
  echo "✅ Đóng gói thành công! File thực thi có thể tìm thấy trong thư mục 'dist/'."
  echo "Tên file: dist/$APP_NAME.exe (trên Windows) hoặc dist/$APP_NAME (trên Linux/macOS)"
else
  echo "❌ Đóng gói thất bại. Vui lòng kiểm tra các thông báo lỗi bên trên."
fi

echo "Hoàn tất."

