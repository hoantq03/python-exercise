import re


def is_vietnamese_phone(phone_number: str) -> bool:
    """
    Kiểm tra xem một chuỗi có phải là số điện thoại Việt Nam hợp lệ hay không.

    Quy tắc:
    - Bắt đầu bằng số 0.
    - Theo sau là đúng 9 chữ số.
    - Tổng cộng có 10 chữ số.

    Args:
        phone_number (str): Chuỗi số điện thoại cần kiểm tra.

    Returns:
        bool: True nếu hợp lệ, False nếu không hợp lệ.
    """
    if not isinstance(phone_number, str):
        return False

    # Biểu thức chính quy: ^0\d{9}$
    # - ^: Bắt đầu chuỗi
    # - 0: Ký tự số 0
    # - \d{9}: Đúng 9 ký tự số (0-9)
    # - $: Kết thúc chuỗi
    pattern = re.compile(r"^0\d{9}$")

    return bool(pattern.match(phone_number))