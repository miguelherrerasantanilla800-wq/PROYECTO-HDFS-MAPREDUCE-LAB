#!/usr/bin/env python3
import sys

from common import parse_transaction, report_invalid

invalid = 0
for line in sys.stdin:
    row = parse_transaction(line)
    if row is None:
        invalid += 1
        continue
    print(f"{row['fecha_hora'][11:13]}\t1")
report_invalid(invalid)
