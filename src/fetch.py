import requests, json
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.runtime.tv/"

def fetch_channels():
    resp = requests.get(SOURCE_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    channels = []
    for item in soup.select(".channel-item"):          # ajuste ao markup real
        name = item.select_one(".channel-name").get_text(strip=True)
        url  = item.select_one("a").get("href")
        cat  = item.select_one(".channel-category").get_text(strip=True).lower()
        channels.append({"name": name, "url": url, "category": cat})
    return channels
