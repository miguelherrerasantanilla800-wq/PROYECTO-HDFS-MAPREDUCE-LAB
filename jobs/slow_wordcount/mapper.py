#!/usr/bin/env python3
"""Mapper LENTO para los experimentos de tolerancia a fallos: WordCount con una pausa por línea
(SLEEP_PER_LINE segundos, por defecto 0.005) para que el job dure minutos y dé tiempo a provocar fallos."""
import os
import re
import sys
import time

sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")
PAUSE = float(os.environ.get("SLEEP_PER_LINE", "0.005"))
TOKEN = re.compile(r"[a-záéíóúñü]+")

n = 0
for line in sys.stdin:
    n += 1
    time.sleep(PAUSE)
    if n % 2000 == 0:   # el estado visible en la UI de YARN y evita el timeout de la tarea
        sys.stderr.write(f"reporter:status:{n} líneas procesadas\n")
    for w in TOKEN.findall(line.lower()):
        print(f"{w}\t1")
