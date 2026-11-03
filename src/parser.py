import json, os
from collections import defaultdict
from unidecode import unidecode

CACHE_FILE = "data/channels.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize(text):
    # minusculo, sem acentos, sem espaços extras
    return unidecode(text).lower().strip()

def merge_categories(cat_list):
    # sinônimos comuns → categoria principal
    synonyms = {
        "entretenimento": ["diversão", "lazer"],
        "esportes": ["sport", "sports", "esportivos"],
        "filmes": ["cinema", "movies"],
        "notícias": ["news", "noticia", "notícias"]
    }
    for main, alts in synonyms.items():
        if cat_list & set(alts):
            return main
    return list(cat_list)[0]          # fallback: primeira encontrada
