#!/usr/bin/env python3
import os
import sys

top_n = int(os.environ.get("TOP_N", "10"))
counts = {}
for line in sys.stdin:
    key, _, value = line.rstrip("\n").partition("\t")
    try:
        counts[key] = counts.get(key, 0) + int(value)
    except ValueError:
        continue

for merchant, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]:
    print(f"{merchant}\t{count}")
