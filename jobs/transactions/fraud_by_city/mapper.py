#!/usr/bin/env python3
import sys

from common import parse_transaction, report_invalid

invalid = 0
for line in sys.stdin:
    row = parse_transaction(line)
    if row is None:
        invalid += 1
        continue
    print(f"{row['ciudad']}\t{row['fraude']},1")
report_invalid(invalid)
