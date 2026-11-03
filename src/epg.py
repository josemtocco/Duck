"""Associação de EPG (tvg-id) aos canais.

O CSV antigo do iptv-org não existe mais no caminho usado originalmente.
Este módulo tenta baixar um mapeamento simples (nome → tvg-id) a partir
de fontes públicas e faz fallback gracioso: se falhar, a lista M3U é
gerada normalmente, apenas sem tvg-id.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from unidecode import unidecode

logger = logging.getLogger(__name__)

EPG_SOURCES = [
    "https://iptv-org.github.io/api/channels.json",
]

CACHE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "epg_cache.json"
)


def _normalize_name(name: str) -> str:
    return unidecode(str(name or "")).lower().strip()


def _download_json(url: str) -> Any | None:
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "TVPlus-EPG/1.0",
                "Accept": "application/json",
            },
        )
        with urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        logger.warning("Falha ao baixar EPG de %s: %s", url, e)
        return None


def _load_cache() -> dict[str, str]:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def _save_cache(data: dict[str, str]) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_epg() -> dict[str, str]:
    """Retorna {nome_normalizado: tvg_id}.

    Usa cache local quando disponível. Se o download falhar, devolve
    dict vazio (a lista ainda é gerada, só sem tvg-id).
    """
    cached = _load_cache()
    if cached:
        return cached

    epg_map: dict[str, str] = {}

    for url in EPG_SOURCES:
        data = _download_json(url)
        if not data:
            continue

        if isinstance(data, list):
            for row in data:
                if not isinstance(row, dict):
                    continue
                name = row.get("name") or row.get("channel_name") or ""
                tvg_id = row.get("id") or row.get("tvg_id") or ""
                if name and tvg_id:
                    epg_map[_normalize_name(name)] = str(tvg_id).strip()
        elif isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict):
                    name = val.get("name", "")
                    if name:
                        epg_map[_normalize_name(name)] = str(key)
                else:
                    epg_map[_normalize_name(str(key))] = str(val)

        if epg_map:
            logger.info("EPG carregado: %d entradas de %s", len(epg_map), url)
            break

    if epg_map:
        _save_cache(epg_map)
    else:
        logger.warning("Nenhuma fonte de EPG respondeu — lista sem tvg-id")

    return epg_map


def attach_epg(
    channels: list[dict[str, Any]], epg_map: dict[str, str]
) -> list[dict[str, Any]]:
    """Adiciona a chave tvg_id a cada canal (string vazia se não houver match)."""
    for ch in channels:
        key = _normalize_name(ch.get("name", ""))
        ch["tvg_id"] = epg_map.get(key, "")
    return channels
