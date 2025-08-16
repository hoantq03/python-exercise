def extract_unique_categories(products_data):
    """
    Trích xuất danh sách các danh mục duy nhất từ dữ liệu sản phẩm.
    Mỗi danh mục là một dictionary có dạng {'categoryName': ..., 'categoryUri': ...}.
    """
    unique_categories = {}

    for product in products_data:
        for category in product.get("categories", []):
            cat_id = category.get("categoryId")
            cat_name = category.get("name")
            cat_uri = category.get("uri")

            # Chỉ xử lý nếu category có ID
            if cat_id is not None:
                unique_categories[cat_id] = {
                    "categoryName": cat_name,
                    "categoryUri": cat_uri
                }

    return list(unique_categories.values())