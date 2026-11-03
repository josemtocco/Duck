import datetime, json, os
from src.fetch import fetch_channels
from src.parser import deduplicate, normalize, merge_categories, load_cache, save_cache, reconcile
from src.epg import load_epg, attach_epg

def build_m3u(channels):
    lines = ["#EXTM3U"]
    # agrupa por categoria já mesclada
    cat_groups = defaultdict(list)
    for ch in channels:
        cat_groups[ch["category"]].append(ch)

    for cat, items in sorted(cat_groups.items()):
        lines.append(f"#EXTGRP:{cat.capitalize()}")
        for ch in items:
            attrs = [
                f'tvg-id="{ch.get("tvg_id","")}"',
                f'tvg-name="{ch["name"]}"',
                f'group-title="{cat.capitalize()}"'
            ]
            line = f'#EXTINF:-1 {" ".join(attrs)},{ch["name"]}'
            lines.append(line)
            lines.append(ch["url"])
    return "\n".join(lines) + "\n"

def main():
    # 1 – coleta
    raw = fetch_channels()

    # 2 – normaliza categorias (sinônimos)
    for ch in raw:
        ch["category"] = merge_categories({normalize(ch["category"])})

    # 3 – deduplica URLs
    uniq = deduplicate(raw)

    # 4 – carrega cache anterior e reconcilia
    cache = load_cache()
    merged = reconcile(uniq, cache)
    save_cache({normalize(c["url"]): c for c in merged})

    # 5 – adiciona EPG
    epg_map = load_epg()
    final = attach_epg(merged, epg_map)

    # 6 – gera .m3u
    m3u_content = build_m3u(final)
    out_path = "TVplus.m3u"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"✅ Lista gerada: {out_path} ({len(final)} canais)")

if __name__ == "__main__":
    main()
