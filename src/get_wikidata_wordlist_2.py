# scripts/get_wikidata_wordlist.py
# -*- coding: utf-8 -*-
"""
Gera listas para o Cytokine Wordle a partir do Wikidata,
filtrando por uma whitelist de citocinas (símbolos HGNC).
- WORDS: soluções (máx. 1000), já com padding para 5
- VALID_GUESSES: todos os palpites válidos (tudo que passou no filtro)

Requisitos:
  pip install SPARQLWrapper

Uso:
  python scripts/get_wikidata_wordlist.py
"""

import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON

# ============================
# CONFIG: forneça a whitelist
# ============================

# Opção A) Arquivo com um símbolo HGNC por linha (recomendado)
WHITELIST_TXT = "/root/cytokine-wordle/gene-wordle/src/constants/cytokinesWhitelist.txt"

# Opção B) Lista embutida (edite/cole seus símbolos aqui se preferir)
CYTOKINES_INLINE = {
    # Exemplo mínimo; substitua pelos seus (ou use o arquivo .txt)
    # 'IL6','TNF','IFNG','TGFB1','IL1A','IL1B','IL10','CXCL8'
}

MAX_SOLUTIONS = 1000
WORDS_OUT = "/root/cytokine-wordle/gene-wordle/src/constants/wordlist_2.ts"
VALID_GUESSES_OUT = "/root/cytokine-wordle/gene-wordle/src/constants/validGuesses_2.ts"


def load_whitelist():
    """Carrega whitelist do arquivo .txt ou do set embutido."""
    wl = set()
    if os.path.exists(WHITELIST_TXT):
        with open(WHITELIST_TXT, "r", encoding="utf-8") as f:
            for line in f:
                sym = line.strip().upper().replace("-", "")
                if sym:
                    wl.add(sym)
    wl.update({s.upper().replace("-", "") for s in CYTOKINES_INLINE})
    if not wl:
        raise SystemExit(
            f"Nenhuma whitelist encontrada.\n"
            f"Crie {WHITELIST_TXT} (um símbolo por linha) ou edite CYTOKINES_INLINE no script."
        )
    return wl


def pad5(s: str) -> str:
    """Preenche à direita com '-' até 5 caracteres."""
    return (s + "-----")[:5]


def main():
    whitelist = load_whitelist()

    # Query quase idêntica ao original (mantém score para ordenar)
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)
    try:
        sparql.setUserAgent("CytokineWordle/1.0 (https://github.com/seu-usuario)")
    except Exception:
        pass

    query = """
    SELECT DISTINCT
      ?item ?gene_symbol ?protein ?sitelink_gene ?sitelink_protein ?score
    WHERE 
    {
      ?item wdt:P353 ?gene_symbol .
      ?item wdt:P688 ?protein .
      ?item wikibase:sitelinks ?sitelink_gene .
      ?protein wikibase:sitelinks ?sitelink_protein .
      BIND(2.5 * ?sitelink_gene + ?sitelink_protein as ?score)
    }
    ORDER BY DESC (?score)
    """
    sparql.setQuery(query)

    data = sparql.query().convert()

    # Mantém ordem de score do resultado (sem precisar ordenar de novo)
    seen = set()          # para evitar duplicatas no output
    all_valid = []        # todos palpites válidos (para VALID_GUESSES)
    solutions = []        # top N (para WORDS)

    for result in data["results"]["bindings"]:
        gene = result["gene_symbol"]["value"].upper().replace("-", "")
        # Filtro: precisa estar na whitelist e ter até 5 caracteres
        if gene in whitelist and len(gene) <= 5:
            padded = pad5(gene)
            if padded not in seen:
                seen.add(padded)
                all_valid.append(padded)
                # limita soluções aos primeiros MAX_SOLUTIONS em ordem de score
                if len(solutions) < MAX_SOLUTIONS:
                    solutions.append(padded)

    if not all_valid:
        raise SystemExit("Nada encontrado: verifique se sua whitelist bate com símbolos HGNC do Wikidata.")

    # Gera arquivos TS
    os.makedirs(os.path.dirname(WORDS_OUT), exist_ok=True)

    with open(WORDS_OUT, "w", encoding="utf-8") as f:
        f.write("export const WORDS = " + json.dumps(solutions, indent=2) + "\n")

    with open(VALID_GUESSES_OUT, "w", encoding="utf-8") as f:
        f.write("export const VALID_GUESSES = " + json.dumps(all_valid, indent=2) + "\n")

    print(f"[ok] WORDS → {WORDS_OUT}  ({len(solutions)} soluções)")
    print(f"[ok] VALID_GUESSES → {VALID_GUESSES_OUT}  ({len(all_valid)} palpites)")

if __name__ == "__main__":
    main()
