#!/usr/bin/env python3
"""Reducer del promedio: categoria<TAB>promedio<TAB>total<TAB>n_ventas"""
import sys

current, s, c = None, 0.0, 0


def emit():
    print(f"{current}\t{s / c:.2f}\t{s:.2f}\t{c}")


for line in sys.stdin:
    key, _, val = line.rstrip("\n").partition("\t")
    a, _, b = val.partition(",")
    if key != current:
        if current is not None:
            emit()
        current, s, c = key, 0.0, 0
    s += float(a)
    c += int(b)
if current is not None:
    emit()
