# Ứng dụng Quản lý Sản phẩm & Web Scraper

Một ứng dụng desktop được xây dựng bằng Python, dùng để quản lý sản phẩm, khách hàng, đơn hàng với các tính năng tự động thu thập dữ liệu sản phẩm (web scraping) theo lịch trình.

## 📜 Mục lục
* [Tính năng chính](#-tính-năng-chính)
* [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
* [⚙️ Hướng dẫn Cài đặt & Cấu hình](#️-hướng-dẫn-cài-đặt--cấu-hình)
  * [1. Clone Repository](#1-clone-repository)
  * [2. Tạo môi trường ảo](#2-tạo-môi-trường-ảo)
  * [3. Cài đặt thư viện](#3-cài-đặt-thư-viện)
  * [4. Cấu hình Biến môi trường (.env)](#4-cấu-hình-biến-môi-trường-env)
* [🚀 Cách chạy ứng dụng](#-cách-chạy-ứng-dụng)
* [📦 Đóng gói thành tệp thực thi (.exe)](#-đóng-gói-thành-tệp-thực-thi-exe)
* [🤝 Đóng góp](#-đóng-góp)
* [📝 Giấy phép](#-giấy-phép)

## ✨ Tính năng chính
*   **Quản lý Sản phẩm:** Giao diện để xem, thêm, sửa, xóa sản phẩm.
*   **Tự động Thu thập Dữ liệu:** Scraper tích hợp để tự động lấy thông tin sản phẩm (điện thoại, laptop) từ các trang web.
*   **Lập lịch Tác vụ:** Sử dụng scheduler để chạy các scraper và cập nhật danh mục định kỳ.
*   **Giao diện Người dùng:** Xây dựng giao diện desktop thân thiện.
*   **Đóng gói:** Dễ dàng đóng gói thành một file `.exe` để chạy trên máy khác mà không cần cài đặt Python.

## 📋 Yêu cầu hệ thống
*   Python 3.8+
*   Git
*   Các thư viện Python được liệt kê trong `requirements.txt`.

## ⚙️ Hướng dẫn Cài đặt & Cấu hình
Thực hiện theo các bước sau để thiết lập môi trường và chạy dự án trên máy của bạn.

### 1. Clone Repository
Mở Terminal hoặc PowerShell và chạy lệnh sau:
```bash
git clone https://github.com/hoantq03/python-exercise.git
cd python-exercise
```



### 2. Tạo môi trường ảo
Việc này giúp cô lập các thư viện của dự án.
```bash
python -m venv venv
```

Kích hoạt môi trường ảo:

**Trên Windows (PowerShell/CMD):**
```bash
.\venv\Scripts\activate
```

**Trên Linux/macOS:**
```bash
source venv/bin/activate
```


Sau khi kích hoạt, bạn sẽ thấy `(venv)` ở đầu dòng lệnh.

### 3. Cài đặt thư viện
Cài đặt tất cả các thư viện cần thiết chỉ bằng một lệnh:
```bash
pip install -r requirements.txt
```

**Tip:** Nếu bạn thêm thư viện mới, hãy cập nhật file `requirements.txt` bằng lệnh: `pip freeze > requirements.txt`

### 4. Cấu hình Biến môi trường (.env)
Đây là bước quan trọng để cấu hình các thông số của ứng dụng mà không cần sửa code.

Tạo một file mới tên là `.env` trong thư mục gốc của dự án.
Sao chép nội dung dưới đây vào file `.env` và tùy chỉnh giá trị nếu cần.

**`.env.example`**

Tài khoản admin để đăng nhập vào các chức năng quản trị
ADMIN_USERNAME=0123456789
ADMIN_PASSWORD=1234567890



--- Cấu hình bật/tắt các module Scraper ---
Đặt là True để bật, False (hoặc bỏ trống) để tắt
PHONE_SCRAPER_ENABLED=True
LAPTOP_SCRAPER_ENABLED=False
UPDATE_CATEGORIES_ENABLED=True



--- Cấu hình thời gian cho Scheduler ---
Khoảng thời gian (giây) để chạy lại các scraper đã bật
SCRAPER_INTERVAL_SECONDS=300



Khoảng thời gian (giây) để chạy lại tác vụ cập nhật danh mục
CATEGORY_UPDATE_INTERVAL_SECONDS=30



--- Cấu hình riêng cho Scraper ---
Số lượng sản phẩm điện thoại cần scrape mỗi lần chạy
NUMBER_SCRAPER_PHONES=100



--- Cấu hình cho mục đích Test ---
Tự động tạo các đơn hàng giả để test. Bật là True, tắt là False
GENERATE_DUMMY_ORDERS=False



**Giải thích chi tiết các biến môi trường:**

| Biến | Ý nghĩa | Giá trị ví dụ       |
| :--- | :--- |:--------------------|
| `ADMIN_USERNAME` | Tên đăng nhập cho tài khoản quản trị viên. | `administrator`     |
| `ADMIN_PASSWORD` | Mật khẩu cho tài khoản quản trị viên. | `Strongp@ssword123` |
| `PHONE_SCRAPER_ENABLED` | Bật (`True`) hoặc tắt (`False`) module tự động cào dữ liệu điện thoại. | `True`              |
| `LAPTOP_SCRAPER_ENABLED` | Bật (`True`) hoặc tắt (`False`) module tự động cào dữ liệu laptop. | `False`             |
| `UPDATE_CATEGORIES_ENABLED` | Bật (`True`) hoặc tắt (`False`) tác vụ tự động cập nhật danh mục sản phẩm. | `True`              |
| `SCRAPER_INTERVAL_SECONDS` | Khoảng thời gian (tính bằng giây) giữa các lần chạy scraper. | `3600` (1 giờ)      |
| `NUMBER_SCRAPER_PHONES` | Số lượng sản phẩm điện thoại tối đa mà scraper sẽ lấy trong một lần chạy. | `100`               |
| `CATEGORY_UPDATE_INTERVAL_SECONDS` | Tần suất (tính bằng giây) để chạy lại tác vụ cập nhật danh mục. | `600` (10 phút)     |
| `GENERATE_DUMMY_ORDERS` | Bật (`True`) nếu bạn muốn hệ thống tự tạo các đơn hàng giả để kiểm thử. | `False`             |

## 🚀 Cách chạy ứng dụng
Đảm bảo môi trường ảo đã được kích hoạt.
Điều hướng đến thư mục gốc của dự án (nơi có file `main.py`).
Nếu bạn chưa có file `.env`, hãy sao chép file mẫu `.env.example` và chỉnh sửa theo nhu cầu của bạn:
```bash
Chạy lệnh:
```bash
python main.py
```


## 📦 Đóng gói thành tệp thực thi (.exe)
Bạn có thể đóng gói toàn bộ ứng dụng thành một file duy nhất để dễ dàng chia sẻ và sử dụng trên các máy Windows khác.

Cài đặt `PyInstaller` (nếu chưa có):
```bash
pip install pyinstaller
```



Chạy script đóng gói:

**Trên Windows (mở bằng PowerShell):**
```bash
.\build_app.ps1
```


**Trên Linux/macOS (mở bằng Terminal):**
```bash
chmod +x build_app.sh
./build_app.sh
```

Sau khi chạy xong, tệp thực thi sẽ nằm trong thư mục `dist/`.

## 🤝 Đóng góp
Mọi đóng góp để cải thiện dự án đều được hoan nghênh! Vui lòng tạo một "Issue" để báo lỗi/đề xuất tính năng hoặc gửi một "Pull Request" với các thay đổi của bạn.

## 📝 Giấy phép
Dự án này được cấp phép theo Giấy phép MIT. Xem chi tiết trong tệp `LICENSE`.
