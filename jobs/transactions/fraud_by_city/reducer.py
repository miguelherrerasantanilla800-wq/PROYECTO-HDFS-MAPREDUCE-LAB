#!/usr/bin/env python3
import sys

current = None
fraud, total = 0, 0


def emit():
    print(f"{current}\t{fraud}\t{total}\t{fraud / total:.6f}")


for line in sys.stdin:
    key, _, value = line.rstrip("\n").partition("\t")
    try:
        fraud_part, total_part = value.split(",", 1)
        fraud_part, total_part = int(fraud_part), int(total_part)
    except ValueError:
        continue
    if key != current:
        if current is not None:
            emit()
        current, fraud, total = key, 0, 0
    fraud += fraud_part
    total += total_part
if current is not None:
    emit()
