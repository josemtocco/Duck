# src/epg.py
import csv, urllib.request, os, json
from urllib.error import HTTPError, URLError

# URL oficial do repositório de EPGs mantido pela comunidade iptv‑org
EPG_URL = "https://raw.githubusercontent.com/iptv-org/epg/master/epg.csv"

# caminho opcional de cache local (evita downloads repetidos)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "epg_cache.json")

def _download_epg():
    """
    Faz o download do CSV. Se houver erro (404, timeout, etc.),
    devolve ``None`` para que o chamador saiba que não há EPG.
    """
    try:
        with urllib.request.urlopen(EPG_URL, timeout=15) as resp:
            # resp é um iterável de linhas de bytes
            return resp.read().decode("utf-8")
    except (HTTPError, URLError) as e:
        # registro opcional no log (no CI fica na saída padrão)
        print(f"⚠️  Falha ao baixar EPG ({e.__class__.__name__}): {e}")
        return None

def _load_cache():
    """Lê o cache local se existir e for válido."""
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
    - Primeiro tenta usar o cache local.
    - Se o cache estiver vazio ou expirado, tenta baixar o CSV.
    - Caso o download falhe, devolve um dicionário vazio (lista M3U será gerada sem EPG).
    """
    # 1️⃣ tenta cache
    cached = _load_cache()
    if cached:
        return cached

    # 2️⃣ tenta download
    csv_text = _download_epg()
    if csv_text is None:
        # falha completa – devolve dicionário vazio
        return {}

    epg_map = {}
    reader = csv.DictReader(csv_text.splitlines())
    for row in reader:
        # normaliza o nome do canal para comparar depois
        name_key = row["channel_name"].strip().lower()
        epg_map[name_key] = row["tvg_id"].strip()

    # 3️⃣ grava cache para próximas execuções
    _save_cache(epg_map)
    return epg_map
