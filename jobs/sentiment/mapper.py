#!/usr/bin/env python3
"""JOB 5 - Clasificación de sentimiento. Entrada: id<TAB>texto. Emite (etiqueta, 1)."""
import sys

from lexicon import classify          # se distribuye con -files

sys.stdin.reconfigure(encoding="utf-8", errors="replace")
for line in sys.stdin:
    _, sep, text = line.rstrip("\n").partition("\t")
    if not sep:
        sys.stderr.write("reporter:counter:Reseñas,invalidas,1\n")
        continue
    print(f"{classify(text)}\t1")
