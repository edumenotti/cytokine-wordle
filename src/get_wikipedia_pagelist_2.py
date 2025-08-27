#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from SPARQLWrapper import SPARQLWrapper, JSON

HERE = os.path.dirname(os.path.abspath(__file__))
WORDLIST_TS = os.path.join(HERE, "constants", "wordlist.ts")
OUT_JSON    = os.path.join(HERE, "constants", "wikipedialist.json")

# User-Agent (recomendado pelo WDQS; pode sobrescrever por env)
USER_AGENT = os.getenv(
    "WDQS_USER_AGENT",
    "CytokineWordle/1.0 (+https://github.com/edumenotti/cytokine-wordle; mailto:menotti.edu@gmail.com)"
)

STRING_RE = re.compile(r"""(['"])(.*?)\1""")

def extract_words_from_ts_array(path: str):
    """Extrai strings do PRIMEIRO array [...] em wordlist.ts (sem parse TS de verdade)."""
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

def main():
    if not os.path.exists(WORDLIST_TS):
        raise SystemExit(f"Não encontrei {WORDLIST_TS}")

    words_padded = extract_words_from_ts_array(WORDLIST_TS)
    if not words_padded:
        raise SystemExit("Não consegui extrair palavras de wordlist.ts")

    symbols = sorted({unpad(w) for w in words_padded})  # HGNC sem padding
    # Monta uma ÚNICA query com VALUES para só esses símbolos
    values = " ".join(f'"{s}"' for s in symbols)

    query = f"""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>
    SELECT DISTINCT ?gene_symbol ?article WHERE {{
      VALUES ?gene_symbol {{ {values} }}
      ?item wdt:P353 ?gene_symbol .
      ?item wdt:P688 ?protein .

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
      BIND(COALESCE(?article_gene, ?article_protein) AS ?article)
    }}
    """

    sparqlwd = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparqlwd.setReturnFormat(JSON)
    try:
        sparqlwd.setUserAgent(USER_AGENT)  # educado com o endpoint
    except Exception:
        pass
    # Importante: deixamos método/timeout no padrão (como o original)
    sparqlwd.setQuery(query)

    data = sparqlwd.query().convert()  # uma única chamada, como o original

    # Monta mapa final (chave = padded 5)
    by_sym = {s: "None" for s in symbols}
    for b in data["results"]["bindings"]:
        sym = b["gene_symbol"]["value"].upper()
        article = b.get("article", {}).get("value") or "None"
        # se vier algo, guarda
        if article != "None":
            by_sym[sym] = article

    wiki_map = {pad5(sym): by_sym[sym] for sym in symbols}

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(wiki_map, f, indent=2)
    print(f"[ok] {OUT_JSON} escrito com {len(wiki_map)} entradas.")

if __name__ == "__main__":
    main()
