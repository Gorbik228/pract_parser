from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time

base_url = "https://1k.by/sport/sportingequipment-bicycles/"
wait = 2

def setup_driver():
    options = webdriver.ChromeOptions()
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def collect_all_links(driver):
    all_links = set()
    visited_pages = set()

    current_url = base_url
    while True:
        if current_url in visited_pages:
            break
        visited_pages.add(current_url)

        driver.get(current_url)
        time.sleep(wait)

        # Собираем все ссылки на странице
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and "1k.by" in href:
                all_links.add(href)
        print(f"[+] Страница: {current_url} — собрано ссылок: {len(all_links)}")

        # Переход на следующую страницу
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a.next")
            current_url = next_btn.get_attribute("href")
            if not current_url:
                break
        except:
            break
        if len(all_links):
            break

    return list(all_links)

def click_through_links(driver, links):
    results = []
    for i, link in enumerate(links):
        try:
            driver.get(link)
            time.sleep(wait)
            status = "OK"
        except (TimeoutException, WebDriverException) as e:
            status = f"ERROR: {str(e)}"
        print(f"[{i+1}/{len(links)}] {link} → {status}")
        results.append((link, status))
    return results

def save_results(results, filename="selenium_results.csv"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("url,status\n")
        for url, status in results:
            f.write(f"{url},{status}\n")
    print(f"\n Результаты сохранены в {filename}")

def main():
    driver = setup_driver()
    try:
        print(" Сбор ссылок...")
        links = collect_all_links(driver)

        print("\n Проверка ссылок...")
        results = click_through_links(driver, links)

        save_results(results)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
#free-proxy-list.net/ru/