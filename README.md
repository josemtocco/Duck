# TV+ / Duck.ai — Gerador de lista M3U

Projeto que coleta canais de uma fonte web, limpa/deduplica, associa EPG (quando disponível) e gera um arquivo `TVplus.m3u` pronto para players IPTV.

Atualização automática via GitHub Actions a cada 6 horas.

## Estrutura

```
.
├── .github/workflows/update.yml   # cron + workflow_dispatch
├── src/
│   ├── __init__.py
│   ├── fetch.py                   # coleta da fonte
│   ├── parser.py                  # limpeza, dedupe, categorias, cache
│   ├── epg.py                     # mapeamento de tvg-id
│   └── generate_m3u.py            # orquestra tudo e gera o .m3u
├── data/                          # cache (channels.json, epg_cache.json)
├── requirements.txt
├── generate.sh                    # script local de teste
└── TVplus.m3u                     # saída (gerada)
```

## Uso local

```bash
# Dependências
python3 -m pip install -r requirements.txt

# Gerar a lista
./generate.sh
# ou
python3 -m src.generate_m3u
```

O arquivo `TVplus.m3u` será criado na raiz do projeto.

## Fonte de canais

Por padrão o coletor aponta para `https://www.runtime.tv/`.  
O site atual **não** expõe uma lista pública de streams no HTML (é um serviço de streaming com app).  

Por isso o `fetch.py` foi escrito de forma **resiliente**:

1. Tenta vários seletores CSS comuns.
2. Se nada for encontrado (ou a rede falhar), usa uma **lista de exemplo** e registra um aviso no log.
3. Assim o pipeline (Actions + cache + M3U) continua funcionando.

### Como apontar para outra fonte

Edite `src/fetch.py`:

- Altere `SOURCE_URL`.
- Ajuste os seletores em `_extract_from_soup()` para o markup real do site.
- Ou substitua `fetch_channels()` por uma função que leia uma API / outro M3U / arquivo local.

## EPG

O módulo tenta baixar o catálogo de canais do [iptv-org](https://iptv-org.github.io/api/channels.json) e preencher `tvg-id`.  
Se a fonte estiver indisponível, a lista é gerada normalmente **sem** `tvg-id`.

## GitHub Actions

O workflow `.github/workflows/update.yml`:

- Roda a cada 6 h e também manualmente (`workflow_dispatch`).
- Gera o M3U e faz commit automático de `TVplus.m3u` + caches em `data/`.

É necessário que o repositório tenha permissão de escrita para o token do Actions (já configurado no YAML com `permissions: contents: write`).

## Observações

- Canais que não aparecem na coleta por mais de um ciclo (~6–12 h) são removidos do cache.
- Categorias são normalizadas (sinônimos: esportes/sport, notícias/news, etc.).
- URLs são deduplicadas após normalização (sem acentos, minúsculas).
