
## Yêu cầu

*   Python 3.x
*   Các thư viện Python (liệt kê trong `requirements.txt`)

## Cài đặt

1.  **Clone repository:**
    ```
    git clone https://github.com/hoantq03/python-exercise.git
    cd python-exercise
    ```
    (Thay thế `your-username` và `your-repo-name` bằng thông tin thực tế của bạn)

2.  **Tạo môi trường ảo (khuyến nghị):**
    ```
    python -m venv venv
    # Trên Windows:
    .\venv\Scripts\activate
    # Trên Linux/macOS:
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện phụ thuộc:**
    ```
    pip install -r requirements.txt
    ```
    Để tạo tệp `requirements.txt`, bạn có thể chạy: `pip freeze > requirements.txt`

## Cách chạy ứng dụng

1.  **Đảm bảo môi trường ảo đã được kích hoạt.**
2.  **Điều hướng đến thư mục gốc của dự án** (thư mục chứa `main.py`).
3.  **Chạy ứng dụng:**
    ```
    python main.py
    ```

## Đóng gói thành tệp thực thi

Ứng dụng này có thể được đóng gói thành một tệp thực thi duy nhất (ví dụ: `.exe` trên Windows) bằng PyInstaller, cho phép chạy mà không cần cài đặt Python.

1.  **Cài đặt PyInstaller:**
    ```
    pip install pyinstaller
    ```

2.  **Sử dụng script đóng gói:**
    *   **Trên Linux/macOS (Terminal):**
        ```
        chmod +x build_app.sh
        ./build_app.sh
        ```
    *   **Trên Windows (PowerShell):**
        ```
        .\build_app.ps1
        ```

3.  **Tệp thực thi** sẽ được tìm thấy trong thư mục `dist/` sau khi quá trình đóng gói hoàn tất.

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo một "Issue" hoặc gửi "Pull Request".

## Giấy phép

Dự án này được cấp phép theo Giấy phép MIT. Xem tệp [LICENSE](LICENSE) để biết thêm chi tiết. <!-- Đảm bảo bạn có một tệp LICENSE -->

---

