#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from typing import List, Set, Tuple

# --- helpers de parsing ---

STRING_RE = re.compile(r"""(['"])(.*?)\1""")  # pega "IL6--" ou 'IL6--'

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def extract_strings_from_ts_array(ts_source: str) -> List[str]:
    """
    Extrai strings do PRIMEIRO array com colchetes '[' ... ']' no arquivo TS.
    Não tenta interpretar TS; só busca o primeiro bloco [ ... ] e coleta strings entre aspas.
    """
    # encontra o primeiro bloco de colchetes balanceado simples
    start = ts_source.find('[')
    if start == -1:
        return []
    # percorre para achar o ']' correspondente (ingênuo, mas suficiente para lista plana)
    depth = 0
    end = -1
    for i, ch in enumerate(ts_source[start:], start=start):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return []
    array_block = ts_source[start:end+1]
    return [m.group(2) for m in STRING_RE.finditer(array_block)]

def extract_strings_from_txt(txt_source: str) -> List[str]:
    out = []
    for line in txt_source.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        out.append(s)
    return out

def load_symbols(path: str) -> List[str]:
    """
    Carrega símbolos de um arquivo .ts (array de strings) OU .txt (um por linha).
    """
    src = read_file(path)
    if path.endswith(".ts") or path.endswith(".tsx"):
        return extract_strings_from_ts_array(src)
    else:
        return extract_strings_from_txt(src)

# --- normalização/padding ---

def normalize_gene_symbol(raw: str) -> str:
    """
    Uppercase, remove espaços, tira hífens somente se estiverem NO MEIO do símbolo original.
    Em seguida, garante 5 caracteres com padding '-' à direita.
    Regras do jogo: 5 chars sempre. Se vier >5, mantemos como está? Não: vamos descartar >5 e avisar.
    """
    s = raw.strip().upper().replace(" ", "")
    # A maior parte das listas já vem sem hífen. Se vier "IL-6", removemos o hífen.
    s = s.replace("-", "")
    if len(s) == 0:
        return ""
    if len(s) < 5:
        s = (s + "-----")[:5]
    elif len(s) > 5:
        # não vamos incluir entradas >5 porque o arquivo .ts usa 5 fixo
        return ""
    return s

def normalize_many(raws: List[str]) -> List[str]:
    out = []
    for r in raws:
        s = normalize_gene_symbol(r)
        if s:
            out.append(s)
    return out

# --- escrita TS ---

def render_ts_array(var_name: str, items: List[str]) -> str:
    """
    Renderiza um arquivo TS no formato:
      export const <VAR> = [
        'ITEM1',
        'ITEM2',
        ...
      ]
    """
    lines = []
    lines.append(f"export const {var_name} = [")
    for it in items:
        lines.append(f"  '{it}',")
    lines.append("]\n")
    return "\n".join(lines)

def backup(path: str) -> str:
    bak = path + ".bak"
    write_file(bak, read_file(path))
    return bak

# --- lógica principal ---

def main():
    ap = argparse.ArgumentParser(description="Mescla citocinas extra em src/constants/validGuesses.ts mantendo formato TS.")
    ap.add_argument("--base", default="src/constants/validGuesses.ts",
                    help="Caminho do validGuesses.ts já existente (base).")
    ap.add_argument("--extra", required=True,
                    help="Arquivo extra com símbolos (ts ou txt). Ex.: data/cytokines_hgnc.txt ou src/constants/wordlist.ts")
    ap.add_argument("--var", default="VALID_GUESSES",
                    help="Nome da constante exportada no arquivo TS base. Default: VALID_GUESSES")
    ap.add_argument("--dry-run", action="store_true",
                    help="Não grava arquivo; só mostra o que seria adicionado.")
    args = ap.parse_args()

    # 1) Carrega base (TS) e extrai lista existente
    if not os.path.exists(args.base):
        print(f"ERRO: não encontrei {args.base}", file=sys.stderr)
        sys.exit(1)
    base_src = read_file(args.base)
    base_items_raw = extract_strings_from_ts_array(base_src)
    base_items = normalize_many(base_items_raw)
    base_set: Set[str] = set(base_items)

    # 2) Carrega extra (ts ou txt), normaliza e filtra 5 chars
    if not os.path.exists(args.extra):
        print(f"ERRO: não encontrei {args.extra}", file=sys.stderr)
        sys.exit(1)
    extra_raw = load_symbols(args.extra)
    extra_items = normalize_many(extra_raw)
    extra_set: Set[str] = set(extra_items)

    # 3) Calcula adições
    additions = sorted(extra_set - base_set)
    merged = sorted(base_set | extra_set)

    print(f"[info] Base: {len(base_set)} itens | Extra (normalizados): {len(extra_set)} | Novos a incluir: {len(additions)}")
    if additions:
        print("[info] Exemplos de adições:", ", ".join(additions[:20]))

    if args.dry_run:
        print("[dry-run] Nada foi escrito.")
        return

    # 4) Reescreve o arquivo base preservando o nome da constante
    #    (não tentamos preservar comentários; fazemos backup)
    bak_path = backup(args.base)
    print(f"[backup] Cópia criada em: {bak_path}")

    new_ts = render_ts_array(args.var, merged)
    write_file(args.base, new_ts)
    print(f"[ok] {args.base} atualizado com {len(merged)} itens.")

if __name__ == "__main__":
    main()
