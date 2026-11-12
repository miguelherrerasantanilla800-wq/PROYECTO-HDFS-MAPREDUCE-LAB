#!/usr/bin/env python3
"""Compara los resultados MapReduce con agregaciones independientes del JSONL."""
import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict


def load_tsv(path):
    with open(path, encoding="utf-8") as source:
        return [line.rstrip("\n").split("\t") for line in source if line.strip()]


def expected_results(data):
    totals_by_category = defaultdict(lambda: [0, 0])
    hours = Counter()
    merchants = Counter()
    fraud_by_city = defaultdict(lambda: [0, 0])
    payments = defaultdict(lambda: [0, 0])
    files = sorted(glob.glob(os.path.join(data, "transactions", "part-*.jsonl")))
    if not files:
        raise FileNotFoundError(f"No hay partes JSONL en {data}/transactions")

    count = 0
    for path in files:
        with open(path, encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                row = json.loads(line)
                amount = row["monto_cop"]
                totals_by_category[row["categoria"]][0] += amount
                totals_by_category[row["categoria"]][1] += 1
                hours[row["fecha_hora"][11:13]] += 1
                merchants[row["merchant"]] += 1
                fraud_by_city[row["ciudad"]][0] += row["fraude"]
                fraud_by_city[row["ciudad"]][1] += 1
                payments[row["metodo_pago"]][0] += amount
                payments[row["metodo_pago"]][1] += 1
                count += 1
    return count, totals_by_category, hours, merchants, fraud_by_city, payments


def check_avg_by_category(path, expected):
    got = {row[0]: (float(row[1]), int(row[2]), int(row[3])) for row in load_tsv(path)}
    ok = set(got) == set(expected) and all(
        got[key][2] == expected[key][1]
        and got[key][1] == expected[key][0]
        and abs(got[key][0] - expected[key][0] / expected[key][1]) < 0.01
        for key in expected
    )
    return ok, f"{len(got)} categorías; {sum(row[2] for row in got.values())} transacciones"


def check_peak_hours(path, expected):
    got = {row[0]: int(row[1]) for row in load_tsv(path)}
    top = ", ".join(f"{hour}h" for hour, _ in expected.most_common(3))
    return got == dict(expected), f"top-3 horas: {top}"


def check_top_merchants(path, expected):
    got = [(row[0], int(row[1])) for row in load_tsv(path)]
    wanted = sorted(expected.items(), key=lambda item: (-item[1], item[0]))[:10]
    return got == wanted, f"{len(got)} comercios; top 1: {got[0][0]} ({got[0][1]})" if got else "vacío"


def check_fraud_by_city(path, expected):
    got = {row[0]: (int(row[1]), int(row[2]), float(row[3])) for row in load_tsv(path)}
    wanted = {city: (fraud, total) for city, (fraud, total) in expected.items()}
    ok = set(got) == set(wanted) and all(
        got[city][:2] == wanted[city]
        and abs(got[city][2] - wanted[city][0] / wanted[city][1]) < 0.000001
        for city in wanted
    )
    return ok, f"{len(got)} ciudades; {sum(row[0] for row in got.values())} transacciones fraudulentas"


def check_payment_methods(path, expected):
    got = {row[0]: (int(row[1]), int(row[2])) for row in load_tsv(path)}
    wanted = {method: (count, amount) for method, (amount, count) in expected.items()}
    return got == wanted, f"{len(got)} métodos; {sum(row[0] for row in got.values())} transacciones"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data")
    parser.add_argument("--results", default="results")
    args = parser.parse_args()

    count, categories, hours, merchants, fraud, payments = expected_results(args.data)
    print(f"[INFO] {count} transacciones leídas para validar")
    checks = [
        ("avg_by_category", check_avg_by_category, (categories,)),
        ("peak_hours", check_peak_hours, (hours,)),
        ("top_merchants", check_top_merchants, (merchants,)),
        ("fraud_by_city", check_fraud_by_city, (fraud,)),
        ("payment_methods", check_payment_methods, (payments,)),
    ]
    failed = 0
    for name, check, expected in checks:
        path = os.path.join(args.results, f"{name}.tsv")
        if not os.path.exists(path):
            print(f"[FAIL] {name:<17} no existe {path}")
            failed += 1
            continue
        try:
            ok, info = check(path, *expected)
        except (OSError, ValueError, IndexError, KeyError) as error:
            ok, info = False, f"error: {error}"
        print(f"[{'PASS' if ok else 'FAIL'}] {name:<17} {info}")
        failed += 0 if ok else 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
