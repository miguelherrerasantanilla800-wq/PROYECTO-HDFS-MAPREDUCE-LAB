#!/usr/bin/env python3
"""JOB 2 - Promedio por clave. Emite categoria<TAB>total_linea,1  (total = cantidad * precio).
Las filas corruptas se descartan y se cuentan con contadores de Hadoop (protocolo reporter:counter),
acumulados y reportados UNA sola vez al final (no uno por fila)."""
import sys

valid = bad = 0
for line in sys.stdin:
    line = line.strip()
    if not line or line.startswith("order_id"):      # cabecera
        continue
    f = line.split(",")
    if len(f) != 7:
        bad += 1
        continue
    try:
        qty, price = int(f[4]), float(f[5])
    except ValueError:
        bad += 1
        continue
    print(f"{f[2]}\t{qty * price:.2f},1")
    valid += 1

sys.stderr.write(f"reporter:counter:Ventas,filas_validas,{valid}\n")
sys.stderr.write(f"reporter:counter:Ventas,filas_malformadas,{bad}\n")
