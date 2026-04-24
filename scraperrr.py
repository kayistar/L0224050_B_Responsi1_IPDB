import csv
import json
import time
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://www.wired.com"
CATEGORY_URL = "https://www.wired.com/category/science/"
TARGET_COUNT = 50


def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # kalau mau headless, buka komentar 2 baris bawah:
    # options.add_argument("--headless=new")
    # options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def collect_article_urls(driver, target_count=50):
    urls = []
    seen = set()
    page_url = CATEGORY_URL

    while len(urls) < target_count and page_url:
        print(f"\nMembuka halaman kategori: {page_url}")
        driver.get(page_url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        for _ in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select('a[href*="/story/"]')

        for a in links:
            href = a.get("href")
            if not href:
                continue

            full_url = urljoin(BASE_URL, href)
            if full_url in seen:
                continue

            seen.add(full_url)
            urls.append(full_url)
            print(f"  URL ditemukan: {full_url}")

            if len(urls) >= target_count:
                break

        next_a = soup.find("a", string=lambda s: s and "Next Page" in s)
        if next_a and next_a.get("href") and len(urls) < target_count:
            page_url = urljoin(BASE_URL, next_a["href"])
        else:
            page_url = None

    return urls[:target_count]


def scrape_article_detail(driver, article_url, scraped_at):
    driver.get(article_url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = ""
    description = ""
    author = ""

    title_tag = soup.find("meta", attrs={"property": "og:title"})
    if title_tag and title_tag.get("content"):
        title = title_tag["content"].strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(" ", strip=True)

    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        description = desc_tag["content"].strip()
    else:
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc and og_desc.get("content"):
            description = og_desc["content"].strip()

    author_tag = soup.find("meta", attrs={"name": "author"})
    if author_tag and author_tag.get("content"):
        author = author_tag["content"].strip()
    else:
        possible_author = soup.find(string=lambda s: s and s.strip().startswith("By"))
        if possible_author:
            author = possible_author.strip()

    if author and not author.startswith("By"):
        author = f"By{author}"

    return {
        "title": title,
        "url": article_url,
        "description": description,
        "author": author,
        "scraped_at": scraped_at,
        "source": "Wired.com"
    }


def save_outputs(articles):
    now = datetime.now()
    session_id = now.strftime("wired_session_%Y%m%d_%H%M%S")
    timestamp = now.isoformat()

    wrapped = [
        {
            "session_id": session_id,
            "timestamp": timestamp,
            "articles_count": len(articles),
            "articles": articles
        }
    ]

    with open("wired_articles.json", "w", encoding="utf-8") as f:
        json.dump(wrapped, f, indent=4, ensure_ascii=False)

    with open("wired_articles.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["title", "url", "description", "author", "scraped_at", "source"]
        )
        writer.writeheader()
        writer.writerows(articles)

    print(f"\nBerhasil simpan {len(articles)} artikel ke wired_articles.json dan wired_articles.csv")


def main():
    driver = make_driver()
    try:
        article_urls = collect_article_urls(driver, TARGET_COUNT)

        scraped_at = datetime.now().isoformat()
        articles = []

        for i, article_url in enumerate(article_urls, start=1):
            print(f"\nScraping detail artikel {i}/{len(article_urls)}")
            item = scrape_article_detail(driver, article_url, scraped_at)
            print(f"  Judul: {item['title']}")
            articles.append(item)

        save_outputs(articles)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()