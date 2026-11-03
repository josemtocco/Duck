# src/epg.py
import csv, json, os, urllib.request
from urllib.error import HTTPError, URLError

# URL oficial do repositório de EPGs mantido pela comunidade iptv‑org
EPG_URL = "https://raw.githubusercontent.com/iptv-org/epg/master/epg.csv"

# caminho opcional de cache local (evita downloads repetidos)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "epg_cache.json")

def _download_epg():
    """Baixa o CSV de EPG. Retorna o conteúdo como string ou None em caso de erro."""
    try:
        with urllib.request.urlopen(EPG_URL, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except (HTTPError, URLError) as e:
        # será exibido nos logs das Actions
        print(f"⚠️  Falha ao baixar EPG ({e.__class__.__name__}): {e}")
        return None

def _load_cache():
    """Lê o cache local (JSON) se existir e for válido."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # cache corrompido – será recriado
            return {}
    return {}

def _save_cache(data):
    """Grava o dicionário de EPG no cache local."""
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_epg():
    """
    Retorna um dicionário ``{nome_do_canal_normalizado: tvg_id}``.
    - Usa cache local quando disponível.
    - Caso o download falhe, devolve dicionário vazio (lista ainda será gerada, só sem tvg‑id).
    """
    cached = _load_cache()
    if cached:
        return cached

    csv_text = _download_epg()
    if csv_text is None:
        return {}

    epg_map = {}
    reader = csv.DictReader(csv_text.splitlines())
    for row in reader:
        # Normaliza o nome do canal para comparação posterior
        name_key = row["channel_name"].strip().lower()
        epg_map[name_key] = row["tvg_id"].strip()

    _save_cache(epg_map)
    return epg_map

# -------------------------------------------------
def attach_epg(channels, epg_map):
    """
    Recebe a lista de canais (cada item é um dict com 'name' etc.) e o
    dicionário retornado por ``load_epg``.
    Adiciona a chave ``tvg_id`` a cada canal, usando o nome normalizado
    para buscar no mapa. Se não houver correspondência, deixa a string vazia.
    """
    for ch in channels:
        key = ch["name"].strip().lower()
        ch["tvg_id"] = epg_map.get(key, "")
    return channels
