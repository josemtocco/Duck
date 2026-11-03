def reconcile(new_list, cache):
    # cache contém: {"url": {"name":..., "category":..., "last_seen": "YYYY‑MM‑DD"}}
    today = datetime.date.today().isoformat()
    for ch in new_list:
        url_key = normalize(ch["url"])
        if url_key in cache:
            cache[url_key].update({"name": ch["name"], "category": ch["category"], "last_seen": today})
        else:
            cache[url_key] = {"name": ch["name"], "category": ch["category"], "last_seen": today}

    # Remove inativos (não vistos nas últimas 2 execuções ≈ 12 h)
    to_del = [u for u, v in cache.items() if (datetime.date.fromisoformat(today) -
                                              datetime.date.fromisoformat(v["last_seen"])).days > 0]
    for u in to_del:
        del cache[u]

    return list(cache.values())
