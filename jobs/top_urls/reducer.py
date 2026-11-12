#!/usr/bin/env python3
"""Reducer Top-N: necesita UN solo reducer (-D mapreduce.job.reduces=1) para ver todas las claves.
Suma por URL y al final imprime las N más visitadas (N = variable de entorno TOP_N)."""
import os
import sys

TOP_N = int(os.environ.get("TOP_N", "10"))
counts = {}
for line in sys.stdin:
    key, _, val = line.rstrip("\n").partition("\t")
    try:
        counts[key] = counts.get(key, 0) + int(val)
    except ValueError:
        continue

for url, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_N]:
    print(f"{url}\t{n}")
