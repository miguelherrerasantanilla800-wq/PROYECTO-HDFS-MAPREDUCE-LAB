#!/usr/bin/env python3
"""Genera datasets sintéticos y reproducibles (semilla fija) para los 5 jobs del taller.

  text/     -> corpus de texto en español (WordCount)
  logs/     -> access logs estilo Apache (horas pico, Top-N URLs)
  sales/    -> ventas CSV con filas corruptas a propósito (promedio por clave)
  reviews/  -> reseñas id<TAB>texto (clasificación positivo/negativo/neutral)

Solo usa la librería estándar.  Uso: generate_data.py --out data [--scale 1.0]
"""
import argparse
import json
import os
import random
from datetime import datetime, timedelta

WORDS = ("de la que el en y a los se del las un por con no una su para es al lo como más pero sus le ya o "
         "este sí porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo nos "
         "durante todos uno les ni contra otros ese eso ante ellos e esto antes algunos qué unos yo otro "
         "otras otra él tanto esa estos mucho nada muchos cual poco ella estar estas algunas algo nosotros "
         "datos clúster nodo bloque réplica archivo sistema distribuido proceso tarea trabajo mapa "
         "reducción servidor memoria disco red falla recuperación lectura escritura clave valor análisis "
         "información tiempo usuario resultado ejecución").split()


def zipf_cum(n):
    total, cum = 0.0, []
    for i in range(n):
        total += 1.0 / (i + 1)
        cum.append(total)
    return cum


# ---------------------------------------------------------------- texto
def gen_text(out, rng, scale):
    d = os.path.join(out, "text")
    os.makedirs(d, exist_ok=True)
    cum = zipf_cum(len(WORDS))
    target = int(3 * 1024 * 1024 * scale)  # ~3 MB por archivo, 4 archivos
    for i in range(4):
        size = 0
        with open(os.path.join(d, f"corpus_{i}.txt"), "w", encoding="utf-8") as f:
            while size < target:
                words = rng.choices(WORDS, cum_weights=cum, k=rng.randint(8, 20))
                line = " ".join(words).capitalize() + rng.choice([".", ".", ",", "!", "?"])
                f.write(line + "\n")
                size += len(line.encode("utf-8")) + 1


# ---------------------------------------------------------------- logs
def gen_logs(out, rng, scale):
    d = os.path.join(out, "logs")
    os.makedirs(d, exist_ok=True)
    hour_w = [1] * 24
    for h, w in {0: .5, 1: .4, 2: .3, 3: .3, 4: .4, 5: .6, 9: 6, 10: 8, 11: 6, 20: 7, 21: 9, 22: 5}.items():
        hour_w[h] = w
    urls = ["/", "/login", "/cart", "/checkout", "/about", "/api/v1/search"] + \
           [f"/products/item-{n}" for n in range(1, 120)]
    ucum = zipf_cum(len(urls))
    base = datetime(2026, 11, 1)
    n_lines = int(50000 * scale)
    for i in range(4):
        with open(os.path.join(d, f"access_{i}.log"), "w") as f:
            for _ in range(n_lines):
                if rng.random() < 0.002:
                    f.write("### linea corrupta del servidor ###\n")
                    continue
                h = rng.choices(range(24), weights=hour_w)[0]
                ts = (base + timedelta(days=rng.randint(0, 6), hours=h,
                                       minutes=rng.randint(0, 59), seconds=rng.randint(0, 59)))
                url = rng.choices(urls, cum_weights=ucum)[0]
                if rng.random() < 0.15:
                    url += f"?utm={rng.randint(1, 9)}"
                status = rng.choices([200, 304, 404, 500], weights=[85, 8, 5, 2])[0]
                ip = f"192.168.{rng.randint(0, 20)}.{rng.randint(1, 254)}"
                f.write(f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S")} +0000] "GET {url} HTTP/1.1" '
                        f'{status} {rng.randint(200, 20000)} "-" "Mozilla/5.0"\n')


# ---------------------------------------------------------------- ventas
def gen_sales(out, rng, scale):
    d = os.path.join(out, "sales")
    os.makedirs(d, exist_ok=True)
    cats = {"electronica": 350, "hogar": 80, "ropa": 45, "libros": 25,
            "deportes": 90, "juguetes": 30, "belleza": 40, "alimentos": 15}
    countries = ["CO", "MX", "AR", "CL", "PE", "ES"]
    n = int(100000 * scale)
    oid = 0
    for part in (1, 2):
        with open(os.path.join(d, f"sales_part{part}.csv"), "w") as f:
            f.write("order_id,date,category,product,quantity,unit_price,country\n")
            for _ in range(n):
                oid += 1
                cat = rng.choice(list(cats))
                price = round(max(1.0, rng.gauss(cats[cat], cats[cat] * 0.25)), 2)
                qty = rng.randint(1, 5)
                date = f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
                row = [str(oid), date, cat, f"{cat}-{rng.randint(1, 40)}", str(qty), f"{price:.2f}", rng.choice(countries)]
                r = rng.random()
                if r < 0.0008:
                    row = row[:5]                 # faltan columnas
                elif r < 0.0016:
                    row[5] = "N/A"                # precio inválido
                elif r < 0.0024:
                    row[4] = "abc"                # cantidad inválida
                f.write(",".join(row) + "\n")


# ---------------------------------------------------------------- reseñas
POS = ["bueno", "excelente", "genial", "fantástico", "increíble", "perfecto", "rápido", "útil"]
NEG = ["malo", "terrible", "horrible", "pésimo", "lento", "defectuoso", "decepcionante", "frágil"]
DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
COLORS = ["rojo", "azul", "verde", "gris", "negro", "blanco"]


def gen_reviews(out, rng, scale):
    d = os.path.join(out, "reviews")
    os.makedirs(d, exist_ok=True)
    n = int(100000 * scale)
    truth = {"positivo": 0, "negativo": 0, "neutral": 0}
    with open(os.path.join(d, "reviews.tsv"), "w", encoding="utf-8") as f:
        for i in range(1, n + 1):
            label = rng.choices(["positivo", "negativo", "neutral"], weights=[45, 30, 25])[0]
            p, q = rng.choice(POS), rng.choice(NEG)
            if label == "positivo":
                text = rng.choice([f"el producto es {p}", f"me parece {p}, lo recomiendo",
                                   f"no es {q}, funciona muy bien", f"servicio {p} y entrega {rng.choice(POS)}"])
            elif label == "negativo":
                text = rng.choice([f"el producto es {q}", f"me parece {q}, no lo recomiendo",
                                   f"no es {p}", "no funciona bien", f"entrega {q} y empaque {rng.choice(NEG)}"])
            else:
                text = rng.choice([f"llegó el {rng.choice(DAYS)}", f"la caja es de color {rng.choice(COLORS)}",
                                   f"pedí el producto el {rng.choice(DAYS)}"])
            truth[label] += 1
            f.write(f"{i}\t{text}\n")
    with open(os.path.join(d, "expected_counts.json"), "w") as f:   # verdad de referencia
        json.dump(truth, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--scale", type=float, default=1.0, help="multiplica el tamaño de los datasets")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    for fn in (gen_text, gen_logs, gen_sales, gen_reviews):
        fn(a.out, rng, a.scale)
        print(f"[ok] {fn.__name__}")


if __name__ == "__main__":
    main()
