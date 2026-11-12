#!/usr/bin/env python3
"""JOB 4 - Top-N URLs. Emite (url_sin_query, 1)."""
import re
import sys

LOG = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) [^"]*" (\d{3}) (\S+)')

for line in sys.stdin:
    m = LOG.match(line)
    if not m:
        sys.stderr.write("reporter:counter:Logs,lineas_invalidas,1\n")
        continue
    print(f"{m.group(4).split('?')[0]}\t1")
