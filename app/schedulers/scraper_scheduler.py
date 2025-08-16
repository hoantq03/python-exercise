import threading
import time
from typing import List
from app.scrapers.base_scraper import BaseScraper


class ScraperScheduler:
    """
    Quản lý việc chạy các tác vụ scraper một cách định kỳ trong một luồng riêng.
    """

    def __init__(self, scrapers_to_run: List[BaseScraper], interval_seconds: int = 5):
        self.scrapers = scrapers_to_run
        self.interval = interval_seconds
        self.is_running = False
        self.thread = None

    def _run_tasks(self):
        """Vòng lặp chạy các tác vụ scraper."""
        while self.is_running:
            print("\n--- [Scheduler] Bắt đầu một phiên làm việc mới ---")
            for scraper_instance in self.scrapers:
                try:
                    scraped_data = scraper_instance.scrape()
                except Exception as e:
                    print(f"Lỗi khi chạy scraper {scraper_instance.__class__.__name__}: {e}")

            print(f"--- [Scheduler] Hoàn thành. Tạm nghỉ {self.interval} giây. ---")
            time.sleep(self.interval)

    def start(self):
        """Bắt đầu chạy scheduler trong một luồng nền."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_tasks, daemon=True)
            self.thread.start()
            print("[Scheduler] Đã được khởi động và đang chạy trong nền.")

    def stop(self):
        self.is_running = False
        print("[Scheduler] Đã nhận tín hiệu dừng.")
