#!/usr/bin/env python3
import sys

current = None
amount, count = 0, 0


def emit():
    print(f"{current}\t{amount},{count}")


for line in sys.stdin:
    key, _, value = line.rstrip("\n").partition("\t")
    try:
        amount_part, count_part = value.split(",", 1)
        amount_part, count_part = int(amount_part), int(count_part)
    except ValueError:
        continue
    if key != current:
        if current is not None:
            emit()
        current, amount, count = key, 0, 0
    amount += amount_part
    count += count_part
if current is not None:
    emit()
