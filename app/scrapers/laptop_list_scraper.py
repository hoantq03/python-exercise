from app.scrapers.base_scraper import BaseScraper
from typing import List, Dict, Any


class LaptopListScraper(BaseScraper):
    """Cào dữ liệu từ trang danh sách laptop."""

    def __init__(self):
        super().__init__("https://cellphones.com.vn/laptop.html")

    def scrape(self) -> List[Dict[str, str]]:
        print("-> Đang cào danh sách laptop...")
        soup = self.fetch_soup()
        if not soup:
            return []

        products_data = []
        product_containers = soup.find_all('div', class_='product-item-info')

        for item in product_containers:
            name = item.find('h3', class_='product__name').text.strip() if item.find('h3',
                                                                                     class_='product__name') else "N/A"
            price = item.find('p', class_='product__price--show').text.strip() if item.find('p',
                                                                                            class_='product__price--show') else "N/A"
            link_tag = item.find('a', class_='product__link')
            detail_url = link_tag['href'] if link_tag else "N/A"
            products_data.append({"name": name, "price": price, "detail_url": detail_url})

        print(f"   Hoàn thành. Tìm thấy {len(products_data)} laptop.")
        return products_data

