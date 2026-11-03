import csv, urllib.request

EPG_URL = "https://raw.githubusercontent.com/iptv-org/epg/master/epg.csv"

def load_epg():
    epg_map = {}
    with urllib.request.urlopen(EPG_URL) as f:
        reader = csv.DictReader(line.decode('utf-8') for line in f)
        for row in reader:
            epg_map[row["channel_name"].lower()] = row["tvg_id"]
    return epg_map

def attach_epg(channels, epg_map):
    for ch in channels:
        key = normalize(ch["name"])
        ch["tvg_id"] = epg_map.get(key, "")
    return channels
