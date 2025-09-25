#обходить все страницы собирать ссылки и потом прокликать все ссылки

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "https://1k.by/sport/sportingequipment-bicycles/"
all_links_file = "all_links.txt"
results_csv_file = "link_check_results.csv"

def fetch_page(url):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def collect_links(soup, current_url, links_set):
    for a in soup.find_all("a", href=True):
        href = urljoin(current_url, a["href"])
        links_set.add(href)

def find_next_page(soup, current_url):
    next_btn = soup.select_one("a.next")
    if next_btn:
        return urljoin(current_url, next_btn["href"])
    return None

def crawl(start_url):
    visited = set()
    to_visit = [start_url]
    all_links = set()

    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)
        try:
            soup = fetch_page(url)
        except requests.RequestException as e:
            print(f"[CRAWL ERROR] {url} -> {e}")
            continue

        collect_links(soup, url, all_links)
        nxt = find_next_page(soup, url)
        if nxt and nxt not in visited:
            to_visit.append(nxt)

    return all_links

def check_url(url):
    try:
        resp = requests.get(url, timeout=10)
        return url, resp.status_code, None
    except requests.RequestException as e:
        return url, None, str(e)

def check_all_links(urls):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url, status, error = future.result()
            if error:
                print(f"[ERROR] {url} -> {error}")
            else:
                print(f"[OK]    {url} -> HTTP {status}")
            results.append((url, status, error))
    return results

def save_links(links, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for link in sorted(links):
            f.write(link + "\n")
    print(f"Ссылки сохранены в {filename} ({len(links)} ссылок)")

def save_results(results, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("url,status,error\n")
        for url, status, error in results:
            status_text = status or ""
            error_text = error.replace(",", " ") if error else ""
            f.write(f"{url},{status_text},{error_text}\n")
    print(f"Результаты сохранены в {filename} ({len(results)})")

def main():
    print("Сбор ссылок...")
    links = crawl(base_url)
    save_links(links, all_links_file)

    print("Проверка ссылок...")
    results = check_all_links(links)
    save_results(results, results_csv_file)

if __name__ == "__main__":
    main()

