"""Limpeza, deduplicação, categorização e cache de canais."""

from __future__ import annotations

import datetime
import json
import os
from typing import Any

from unidecode import unidecode

CACHE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "channels.json"
)


def normalize(text: str) -> str:
    """Minúsculo, sem acentos e sem espaços extras."""
    return unidecode(str(text or "")).lower().strip()


def deduplicate(channels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove entradas com a mesma URL (após normalização).
    Mantém a primeira ocorrência encontrada.
    """
    seen: dict[str, dict[str, Any]] = {}
    unique: list[dict[str, Any]] = []
    for ch in channels:
        key = normalize(ch.get("url", ""))
        if not key or key in seen:
            continue
        seen[key] = ch
        unique.append(ch)
    return unique


def merge_categories(cat_set: set[str]) -> str:
    """Recebe um set de categorias (já normalizadas) e devolve
    a categoria principal, juntando sinônimos.
    """
    if not cat_set:
        return "outros"

    synonyms: dict[str, set[str]] = {
        "entretenimento": {"diversao", "lazer", "entretenimento"},
        "esportes": {"sport", "sports", "esportivos", "esporte"},
        "filmes": {"cinema", "movies", "filme"},
        "noticias": {"news", "noticia", "noticias", "jornalismo"},
        "abertos": {"aberto", "tv aberta", "aberta", "free"},
        "series": {"serie", "series"},
        "infantil": {"kids", "criancas", "infantil", "desenho"},
        "documentarios": {"doc", "documentario", "docs"},
        "musica": {"music", "musical"},
    }

    normalized = {normalize(c) for c in cat_set}

    for main, alts in synonyms.items():
        if normalized & alts:
            return main

    return next(iter(normalized)) or "outros"


def load_cache() -> dict[str, Any]:
    """Lê o cache JSON. Arquivo inexistente/vazio/inválido → dict vazio."""
    if not os.path.exists(CACHE_FILE):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(data: dict[str, Any]) -> None:
    """Grava o dicionário de cache no arquivo JSON."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reconcile(
    new_list: list[dict[str, Any]], cache: dict[str, Any]
) -> list[dict[str, Any]]:
    """Mantém canais já existentes (atualiza last_seen),
    insere novos e remove os que não apareceram na última coleta
    (diferença de dias > 0 ≈ 1 ciclo de 6 h).
    """
    today = datetime.date.today().isoformat()

    for ch in new_list:
        url_key = normalize(ch.get("url", ""))
        if not url_key:
            continue
        cache[url_key] = {
            "name": ch.get("name", "Sem nome"),
            "url": ch.get("url", ""),
            "category": ch.get("category", "outros"),
            "last_seen": today,
        }

    to_remove = []
    for key, val in cache.items():
        try:
            last = datetime.date.fromisoformat(val.get("last_seen", today))
            diff = datetime.date.fromisoformat(today) - last
            if diff.days > 0:
                to_remove.append(key)
        except (ValueError, TypeError):
            to_remove.append(key)

    for key in to_remove:
        del cache[key]

    return list(cache.values())
