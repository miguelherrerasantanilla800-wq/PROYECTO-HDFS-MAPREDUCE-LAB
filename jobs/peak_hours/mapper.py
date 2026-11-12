#!/usr/bin/env python3
"""JOB 3 - Horas pico. Extrae la hora de cada petición del access log: emite (HH, 1)."""
import re
import sys

LOG = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) [^"]*" (\d{3}) (\S+)')

for line in sys.stdin:
    m = LOG.match(line)
    if not m:
        sys.stderr.write("reporter:counter:Logs,lineas_invalidas,1\n")
        continue
    hour = m.group(2)[12:14]          # 12/Nov/2026:09:15:32 +0000 -> "09"
    print(f"{hour}\t1")
