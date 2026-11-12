#!/usr/bin/env python3
"""Lectura y validación común de registros del dataset de transacciones."""
import json
import re

HOUR = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def parse_transaction(line):
    try:
        row = json.loads(line)
    except (TypeError, ValueError):
        return None
    if not isinstance(row, dict):
        return None
    if not isinstance(row.get("categoria"), str) or not row["categoria"]:
        return None
    if not isinstance(row.get("merchant"), str) or not row["merchant"]:
        return None
    if not isinstance(row.get("metodo_pago"), str) or not row["metodo_pago"]:
        return None
    if not isinstance(row.get("ciudad"), str) or not row["ciudad"]:
        return None
    if not isinstance(row.get("fecha_hora"), str) or not HOUR.fullmatch(row["fecha_hora"]):
        return None
    if type(row.get("monto_cop")) is not int or row["monto_cop"] < 0:
        return None
    if type(row.get("fraude")) is not int or row["fraude"] not in (0, 1):
        return None
    return row


def report_invalid(count):
    if count:
        import sys
        sys.stderr.write(f"reporter:counter:Transacciones,registros_invalidos,{count}\n")
