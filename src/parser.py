# src/parser.py
import os, json, datetime
from collections import defaultdict
from unidecode import unidecode

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "channels.json")

# -------------------------------------------------
def normalize(text: str) -> str:
    """Minusculo, sem acentos e sem espaços extras."""
    return unidecode(text).lower().strip()

# -------------------------------------------------
def deduplicate(channels):
    """
    Remove entradas com a mesma URL (após normalização).
    Mantém a primeira ocorrência encontrada.
    """
    seen = {}
    unique = []
    for ch in channels:
        key = normalize(ch["url"])
        if key not in seen:
            seen[key] = ch
            unique.append(ch)
    return unique

# -------------------------------------------------
def merge_categories(cat_set):
    """
    Recebe um *set* de categorias (já normalizadas) e devolve
    a categoria principal, juntando sinônimos.
    """
    synonyms = {
        "entretenimento": {"diversão", "lazer"},
        "esportes": {"sport", "sports", "esportivos"},
        "filmes": {"cinema", "movies"},
        "notícias": {"news", "noticia", "notícias"},
    }

    for main, alts in synonyms.items():
        if cat_set & alts:
            return main

    import json, os, datetime
from json import JSONDecodeError

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "channels.json")

def load_cache():
    """
    Lê o cache JSON.
    - Se o arquivo não existir → devolve dict vazio.
    - Se o arquivo existir, mas estiver vazio ou inválido → devolve dict vazio
      e sobrescreve o arquivo na primeira gravação.
    """
    if not os.path.exists(CACHE_FILE):
        # cria o diretório caso ainda não exista
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            # arquivos vazios retornam "" → json.loads falha; tratamos aqui
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (JSONDecodeError, OSError):
        # Caso o JSON esteja corrompido, ignora e começa do zero
        return {}

def save_cache(data):
    """Grava o dicionário de cache no arquivo JSON."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------------------------------
def reconcile(new_list, cache):
    """
    - Mantém canais já existentes (atualiza data de última visita).
    - Insere novos canais.
    - Remove canais que não apareceram na última coleta (12 h = 2 ciclos).
    """
    today = datetime.date.today().isoformat()

    # Atualiza ou adiciona
    for ch in new_list:
        url_key = normalize(ch["url"])
        cache[url_key] = {
            "name": ch["name"],
            "category": ch["category"],
            "last_seen": today,
        }

    # Remove canais não vistos nas duas últimas execuções (12 h)
    to_remove = []
    for key, val in cache.items():
        last = datetime.date.fromisoformat(val["last_seen"])
        diff = datetime.date.fromisoformat(today) - last
        if diff.days > 0:          # >0 => não apareceu na última coleta
            to_remove.append(key)

    for key in to_remove:
        del cache[key]

    # Converte o dicionário de volta para lista de dicts
    return list(cache.values())
