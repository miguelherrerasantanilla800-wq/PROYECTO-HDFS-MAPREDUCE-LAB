#!/usr/bin/env python3
"""JOB 1 - WordCount. Emite (palabra, 1) por cada palabra en minúsculas."""
import re
import sys

sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")
TOKEN = re.compile(r"[a-záéíóúñü]+")

for line in sys.stdin:
    for w in TOKEN.findall(line.lower()):
        print(f"{w}\t1")
