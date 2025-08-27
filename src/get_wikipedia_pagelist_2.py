#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import time
import random
from textwrap import dedent
from SPARQLWrapper import SPARQLWrapper, JSON

HERE = os.path.dirname(os.path.abspath(__file__))
WORDLIST_TS = os.path.join(HERE, "constants", "wordlist.ts")
OUT_JSON = os.path.join(HERE, "constants", "wikipedialist.json")

# Parametrizável por ambiente
CHUNK_SIZE   = int(os.getenv("WDQS_CHUNK", "30"))   # tente 20 se ainda der 504
MAX_RETRIES  = int(os.getenv("WDQS_RETRIES", "4"))
TIMEOUT_SECS = int(os.getenv("WDQS_TIMEOUT", "60"))
SLEEP_BASE   = float(os.getenv("WDQS_SLEEP", "1.2"))  # pausa entre blocos
STRING_RE = re.compile(r"""(['"])(.*?)\1""")

def extract_words_from_ts_array(path: str):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    start = src.find('[')
    if start == -1:
        return []
    depth = 0
    end = -1
    for i, ch in enumerate(src[start:], start=start):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return []
    block = src[start:end+1]
    return [m.group(2) for m in STRING_RE.finditer(block)]

def unpad(s: str) -> str:
    return s.replace("-", "").upper()

def pad5(s: str) -> str:
    return (s + "-----")[:5]

def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def run_block_query(symbols_block):
    values = " ".join(f'"{s}"' for s in symbols_block)
    query = dedent(f"""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>
    SELECT ?gene_symbol ?article_gene ?article_protein WHERE {{
      VALUES ?gene_symbol {{ {values} }}
      ?item wdt:P353 ?gene_symbol .
      OPTIONAL {{ ?item wdt:P688 ?protein . }}

      OPTIONAL {{
        ?article_gene schema:about ?item ;
                      schema:inLanguage "en" .
        FILTER (STRSTARTS(STR(?article_gene), "https://en.wikipedia.org/"))
      }}
      OPTIONAL {{
        ?article_protein schema:about ?protein ;
                         schema:inLanguage "en" .
        FILTER (STRSTARTS(STR(?article_protein), "https://en.wikipedia.org/"))
      }}
    }}
    """).strip()

    sparqlwd = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparqlwd.setReturnFormat(JSON)
    sparqlwd.setMethod("POST")        # evita URL gigante; mais estável
    sparqlwd.setTimeout(TIMEOUT_SECS) # timeout explícito
    sparqlwd.setQuery(query)

    # Retentativas com backoff exponencial + jitter
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return sparqlwd.query().convert()
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            # espera crescente com jitter
            wait = SLEEP_BASE * (2 ** (attempt - 1)) + random.uniform(0, 0.4)
            print(f"[warn] WDQS falhou (tentativa {attempt}/{MAX_RETRIES}): {e}. Retentando em ~{wait:.1f}s…")
            time.sleep(wait)

def main():
    if not os.path.exists(WORDLIST_TS):
        raise SystemExit(f"Não encontrei {WORDLIST_TS}")

    words_padded = extract_words_from_ts_array(WORDLIST_TS)
    if not words_padded:
        raise SystemExit("Não consegui extrair palavras de wordlist.ts")

    symbols = sorted({unpad(w) for w in words_padded})  # HGNC sem padding

    by_sym = {s: "None" for s in symbols}

    total_blocks = (len(symbols) + CHUNK_SIZE - 1) // CHUNK_SIZE
    for bi, block in enumerate(chunked(symbols, CHUNK_SIZE), start=1):
        print(f"[info] Bloco {bi}/{total_blocks} (tamanho {len(block)})…")
        data = run_block_query(block)
        for b in data["results"]["bindings"]:
            sym = b["gene_symbol"]["value"].upper()
            art_gene = b.get("article_gene", {}).get("value")
            art_prot = b.get("article_protein", {}).get("value")
            article = art_gene or art_prot or "None"
            # atualiza só se melhor que "None"
            if by_sym.get(sym, "None") == "None" and article != "None":
                by_sym[sym] = article
        # pausa educada entre blocos
        time.sleep(SLEEP_BASE)

    wiki_map = {pad5(sym): by_sym[sym] for sym in symbols}

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(wiki_map, f, indent=2)
    print(f"[ok] {OUT_JSON} escrito com {len(wiki_map)} entradas.")

if __name__ == "__main__":
    main()
