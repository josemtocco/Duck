"""Gera o arquivo TVplus.m3u a partir dos canais coletados."""

from __future__ import annotations

import logging
import os
import sys
from collections import defaultdict
from typing import Any

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.epg import attach_epg, load_epg
from src.fetch import fetch_channels
from src.parser import (
    deduplicate,
    load_cache,
    merge_categories,
    normalize,
    reconcile,
    save_cache,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_m3u(channels: list[dict[str, Any]]) -> str:
    lines = ["#EXTM3U"]
    cat_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for ch in channels:
        cat = ch.get("category") or "outros"
        cat_groups[cat].append(ch)

    for cat, items in sorted(cat_groups.items()):
        group = cat.capitalize()
        lines.append(f"#EXTGRP:{group}")
        for ch in sorted(items, key=lambda x: x.get("name", "").lower()):
            name = ch.get("name", "Sem nome")
            url = ch.get("url", "")
            tvg_id = ch.get("tvg_id", "")
            attrs = [
                f'tvg-id="{tvg_id}"',
                f'tvg-name="{name}"',
                f'group-title="{group}"',
            ]
            lines.append(f'#EXTINF:-1 {" ".join(attrs)},{name}')
            lines.append(url)

    return "\n".join(lines) + "\n"


def main() -> None:
    logger.info("1/6 — Coletando canais…")
    raw = fetch_channels()

    logger.info("2/6 — Normalizando categorias…")
    for ch in raw:
        cat = ch.get("category") or "outros"
        ch["category"] = merge_categories({normalize(cat)})

    logger.info("3/6 — Deduplicando URLs…")
    uniq = deduplicate(raw)

    logger.info("4/6 — Reconciliando com cache…")
    cache = load_cache()
    merged = reconcile(uniq, cache)
    save_cache(
        {
            normalize(c.get("url", "")): {
                "name": c.get("name"),
                "url": c.get("url"),
                "category": c.get("category"),
                "last_seen": c.get("last_seen"),
            }
            for c in merged
            if c.get("url")
        }
    )

    logger.info("5/6 — Associando EPG…")
    epg_map = load_epg()
    final = attach_epg(merged, epg_map)

    logger.info("6/6 — Gerando M3U…")
    m3u_content = build_m3u(final)
    out_path = os.path.join(_ROOT, "TVplus.m3u")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    logger.info("✅ Lista gerada: %s (%d canais)", out_path, len(final))


if __name__ == "__main__":
    main()
