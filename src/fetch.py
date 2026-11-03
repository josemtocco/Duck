"""Coleta canais da fonte configurada.

A fonte padrão (runtime.tv) não expõe uma lista pública de streams no HTML.
Este módulo tenta extrair canais de forma resiliente e, se nada for
encontrado, usa uma lista de exemplo para que o pipeline continue funcionando
(útil para testes locais e GitHub Actions).
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOURCE_URL = "https://www.runtime.tv/"
REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def _sample_channels() -> list[dict[str, Any]]:
    """Lista mínima de exemplo para o pipeline não falhar quando a fonte
    não retorna canais (ou o HTML mudou)."""
    return [
        {
            "name": "Exemplo - Globo (demo)",
            "url": "https://example.com/stream/globo.m3u8",
            "category": "abertos",
        },
        {
            "name": "Exemplo - SporTV (demo)",
            "url": "https://example.com/stream/sportv.m3u8",
            "category": "esportes",
        },
        {
            "name": "Exemplo - News (demo)",
            "url": "https://example.com/stream/news.m3u8",
            "category": "notícias",
        },
    ]


def _extract_from_soup(soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
    """Tenta vários seletores comuns. Ajuste conforme o markup real da fonte."""
    channels: list[dict[str, Any]] = []

    for item in soup.select(".channel-item, .channel, [data-channel], .card-channel"):
        name_el = item.select_one(
            ".channel-name, .name, .title, h2, h3, [data-name]"
        )
        link_el = item.select_one("a[href]")
        cat_el = item.select_one(
            ".channel-category, .category, .group, [data-category]"
        )

        if not name_el or not link_el:
            continue

        name = name_el.get_text(strip=True)
        href = link_el.get("href") or ""
        if not name or not href:
            continue

        url = urljoin(base_url, href)
        cat = (cat_el.get_text(strip=True) if cat_el else "outros").lower()

        channels.append({"name": name, "url": url, "category": cat})

    if not channels:
        for a in soup.select("a[href]"):
            href = a.get("href") or ""
            text = a.get_text(strip=True)
            if not text or len(text) < 2:
                continue
            lower = href.lower()
            if any(ext in lower for ext in (".m3u8", ".m3u", "/live/", "/stream/")):
                channels.append(
                    {
                        "name": text,
                        "url": urljoin(base_url, href),
                        "category": "outros",
                    }
                )

    return channels


def fetch_channels() -> list[dict[str, Any]]:
    """Baixa a página da fonte e extrai canais.

    Em caso de falha de rede ou de nenhum canal encontrado, devolve a lista
    de exemplo e registra um aviso no log.
    """
    try:
        resp = requests.get(
            SOURCE_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Falha ao acessar %s: %s — usando lista de exemplo", SOURCE_URL, exc)
        return _sample_channels()

    soup = BeautifulSoup(resp.text, "lxml")
    channels = _extract_from_soup(soup, SOURCE_URL)

    if not channels:
        logger.warning(
            "Nenhum canal extraído de %s (markup pode ter mudado). "
            "Usando lista de exemplo. Ajuste os seletores em src/fetch.py.",
            SOURCE_URL,
        )
        return _sample_channels()

    logger.info("Coletados %d canais de %s", len(channels), SOURCE_URL)
    return channels


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_channels()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\nTotal: {len(data)} canais")
