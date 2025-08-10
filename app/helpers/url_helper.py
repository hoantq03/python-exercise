def generate_image_variants(base_url: str, count: int) -> list[str]:
    """
    Tạo ra một danh sách các biến thể URL hình ảnh bằng cách thêm hậu tố số.

    Hàm này sẽ tách URL tại dấu chấm cuối cùng, thêm vào các hậu tố dạng "-1", "-2",...
    và sau đó ghép lại với phần mở rộng.

    Args:
        base_url: URL gốc của hình ảnh.
        count: Số lượng biến thể cần tạo.

    Returns:
        Một danh sách các chuỗi URL đã được biến đổi.
    """
    try:
        last_dot_index = base_url.rindex('.')
        base_name = base_url[:last_dot_index]
        extension = base_url[last_dot_index:] # Bao gồm cả dấu '.'
    except ValueError:
        base_name = base_url
        extension = ""

    variant_urls = [f"{base_name}-{i}{extension}" for i in range(1, count + 1)]

    return variant_urls