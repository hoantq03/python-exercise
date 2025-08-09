from app.scrapers.base_scraper import BaseScraper
from typing import List, Dict, Any

class PhoneDetailScraper(BaseScraper):
    """Cào dữ liệu chi tiết của một sản phẩm từ URL của nó."""

    def __init__(self, product_url: str):
        # URL được truyền vào khi khởi tạo
        super().__init__(product_url)

    def scrape(self) -> Dict[str, str]:
        print(f"-> Đang cào chi tiết sản phẩm từ: {self.url}")
        soup = self.fetch_soup()
        if not soup:
            return {}

        tech_specs = {}
        info_table = soup.find('div', id='technicalInfo')
        if info_table:
            rows = info_table.find_all('li', class_='technical-info__item')
            for row in rows:
                title = row.find('p', class_='technical-info__title').text.strip()
                value = row.find('div', class_='technical-info__content').text.strip()
                tech_specs[title] = value

        print(f"   Hoàn thành. Tìm thấy {len(tech_specs)} thông số kỹ thuật.")
        return tech_specs
