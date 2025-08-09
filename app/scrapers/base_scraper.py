# file: scrapers.py

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any


class BaseScraper:
    """
    Lớp cơ sở chứa logic chung cho việc gửi request và phân tích HTML.
    Mỗi scraper con sẽ kế thừa từ lớp này.
    """

    def __init__(self, url: str):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        print(f"[{self.__class__.__name__}] đã được khởi tạo với URL: {self.url}")

    def fetch_soup(self) -> BeautifulSoup:
        """Gửi yêu cầu HTTP đến URL và trả về đối tượng BeautifulSoup."""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi truy cập URL {self.url}: {e}")
            return None

    def scrape(self) -> Any:
        """
        Phương thức trừu tượng mà mỗi lớp scraper con phải triển khai.
        Đây là nơi logic bóc tách dữ liệu chính được viết.
        """
        raise NotImplementedError("Lớp con phải định nghĩa phương thức scrape()")

