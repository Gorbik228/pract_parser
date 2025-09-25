import asyncio
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Set, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://1k.by/sport/sportingequipment-bicycles/"
DELAY = 2.0                 
WORKER_COUNT = 3            
COLLECTOR_TIMEOUT = 30  
CSV_FILENAME = "asinc_check_results.csv"

class BrowserFactory:
    @staticmethod
    def create_driver() -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


class Collector:
    def __init__(self, base_url: str, delay: float = 2.0):
        self.base_url = base_url
        self.delay = delay
        self.driver = None

    def _setup(self):
        if self.driver is None:
            self.driver = BrowserFactory.create_driver()

    def _teardown(self):
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def collect_links_blocking(self, timeout: float = 30.0) -> List[str]:
        self._setup()
        all_links: Set[str] = set()
        visited_pages: Set[str] = set()
        current_url = self.base_url
        start_time = time.time()

        while True:
            if current_url in visited_pages:
                break
            if time.time() - start_time > timeout:
                break
            visited_pages.add(current_url)

            try:
                self.driver.get(current_url)
            except Exception:
                break
            time.sleep(self.delay)

            anchors = self.driver.find_elements(By.TAG_NAME, "a")
            for a in anchors:
                href = a.get_attribute("href")
                if href and "1k.by" in href:
                    all_links.add(href)
            print(f"[Collector] Страница: {current_url} — собрано ссылок: {len(all_links)}")

            # попытка найти кнопку "next"
            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.next")
                next_href = next_btn.get_attribute("href")
                if not next_href:
                    break
                current_url = next_href
            except Exception:
                break

        self._teardown()
        return sorted(all_links)

    async def collect_links(self, loop: asyncio.AbstractEventLoop, executor: ThreadPoolExecutor, timeout: float = COLLECTOR_TIMEOUT) -> List[str]:
        return await loop.run_in_executor(executor, self.collect_links_blocking, timeout)


class Worker:
    def __init__(self, worker_id: int, delay: float = 2.0):
        self.worker_id = worker_id
        self.delay = delay
        self.driver = BrowserFactory.create_driver()

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def check_link_blocking(self, url: str) -> Tuple[str, str]:
        try:
            self.driver.get(url)
            time.sleep(self.delay)
            status = "OK"
        except (TimeoutException, WebDriverException) as e:
            status = f"ERROR: {e.__class__.__name__}"
        except Exception as e:
            status = f"ERROR: {e.__class__.__name__}"
        print(f"[Worker {self.worker_id}] {url} -> {status}")
        return url, status


class WorkerPool:
    def __init__(self, worker_count: int, delay: float = 2.0):
        self.worker_count = worker_count
        self.delay = delay
        self.workers: List[Worker] = []

    async def __aenter__(self):
        # Создаем воркеров в отдельном потоке, но конструкция синхронная — делаем здесь
        for i in range(self.worker_count):
            self.workers.append(Worker(worker_id=i + 1, delay=self.delay))
        return self

    async def __aexit__(self, exc_type, exc, tb):
        for w in self.workers:
            w.close()
        self.workers = []

    async def run_checks(self, links: List[str], loop: asyncio.AbstractEventLoop, executor: ThreadPoolExecutor) -> List[Tuple[str, str]]:
        results: List[Tuple[str, str]] = []
        queue = asyncio.Queue()
        for link in links:
            await queue.put(link)

        async def worker_task(worker: Worker):
            while not queue.empty():
                try:
                    url = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                # запускаем блокирующий переход в executor
                res = await loop.run_in_executor(executor, worker.check_link_blocking, url)
                results.append(res)
                queue.task_done()

        tasks = [asyncio.create_task(worker_task(w)) for w in self.workers]
        await asyncio.gather(*tasks)
        return results


def save_results(results: List[Tuple[str, str]], filename: str = CSV_FILENAME):
    header = ["ID", "URL", "Status", "Timestamp"]
    file_exists = os.path.isfile(filename)
    next_id = 1
    if file_exists:
        # определяем следующий id
        with open(filename, "r", encoding="utf-8", newline="") as f:
            reader = list(csv.reader(f))
            if len(reader) > 1:
                try:
                    last_row = reader[-1]
                    last_id = int(last_row[0])
                    next_id = last_id + 1
                except Exception:
                    pass

    with open(filename, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        for url, status in results:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([next_id, url, status, timestamp])
            next_id += 1
    print(f"[Saver] Результаты сохранены в {filename}")


async def main_async():
    loop = asyncio.get_running_loop()
    # Executor для блокирующих задач Selenium
    with ThreadPoolExecutor(max_workers=WORKER_COUNT + 1) as executor:
        # 1) Сбор ссылок
        collector = Collector(base_url=BASE_URL, delay=DELAY)
        print("[Main] Начинаем сбор ссылок...")
        links = await collector.collect_links(loop, executor, COLLECTOR_TIMEOUT)
        print(f"[Main] Собрано ссылок: {len(links)}")

        if not links:
            print("[Main] Ссылки не найдены. Выход.")
            return

        # 2) Проверка ссылок параллельно воркерами
        async with WorkerPool(worker_count=WORKER_COUNT, delay=DELAY) as pool:
            print("[Main] Начинаем проверку ссылок воркерами...")
            results = await pool.run_checks(links, loop, executor)

        # 3) Сохранение результатов
        save_results(results, CSV_FILENAME)


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n[Main] Прервано пользователем.")


if __name__ == "__main__":
    main()
