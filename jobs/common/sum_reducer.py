#!/usr/bin/env python3
"""Reducer/combiner genérico: suma enteros por clave.  Entrada ordenada por clave: clave<TAB>n"""
import sys

current, total = None, 0
for line in sys.stdin:
    key, _, val = line.rstrip("\n").partition("\t")
    try:
        n = int(val)
    except ValueError:
        continue
    if key == current:
        total += n
    else:
        if current is not None:
            print(f"{current}\t{total}")
        current, total = key, n
if current is not None:
    print(f"{current}\t{total}")
