def deduplicate(channels):
    seen = {}
    unique = []
    for ch in channels:
        key = normalize(ch["url"])
        if key not in seen:
            seen[key] = ch
            unique.append(ch)
    return unique
