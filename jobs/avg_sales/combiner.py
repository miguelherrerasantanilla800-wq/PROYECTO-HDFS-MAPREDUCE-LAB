#!/usr/bin/env python3
"""Combiner del promedio: suma parciales (suma,cuenta). Mismo formato de salida que el mapper,
porque el promedio NO es asociativo: hay que propagar (suma, cuenta), nunca promedios parciales."""
import sys

current, s, c = None, 0.0, 0
for line in sys.stdin:
    key, _, val = line.rstrip("\n").partition("\t")
    a, _, b = val.partition(",")
    if key != current:
        if current is not None:
            print(f"{current}\t{s:.2f},{c}")
        current, s, c = key, 0.0, 0
    s += float(a)
    c += int(b)
if current is not None:
    print(f"{current}\t{s:.2f},{c}")
