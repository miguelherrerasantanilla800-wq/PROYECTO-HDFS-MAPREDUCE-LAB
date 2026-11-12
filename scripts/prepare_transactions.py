#!/usr/bin/env python3
"""Convierte el arreglo JSON de transacciones a partes JSONL aptas para Hadoop."""
import argparse
import glob
import json
import os
import tempfile

READ_SIZE = 1024 * 1024
RECORDS_PER_PART = 100_000


def json_array_items(path):
    decoder = json.JSONDecoder()
    with open(path, encoding="utf-8") as source:
        buffer = ""
        position = 0
        eof = False

        def fill():
            nonlocal buffer, eof
            chunk = source.read(READ_SIZE)
            if chunk:
                buffer += chunk
            else:
                eof = True

        while not buffer and not eof:
            fill()
        while position < len(buffer) and buffer[position].isspace():
            position += 1
        if position == len(buffer) or buffer[position] != "[":
            raise ValueError("El dataset debe ser un arreglo JSON.")
        position += 1

        first = True
        while True:
            while True:
                while position < len(buffer) and buffer[position].isspace():
                    position += 1
                if position < len(buffer):
                    break
                if eof:
                    raise ValueError("El arreglo JSON terminó antes de cerrar.")
                buffer, position = "", 0
                fill()

            if buffer[position] == "]":
                position += 1
                if buffer[position:].strip():
                    raise ValueError("Hay contenido adicional después del arreglo JSON.")
                if source.read().strip():
                    raise ValueError("Hay contenido adicional después del arreglo JSON.")
                return
            if not first:
                if buffer[position] != ",":
                    raise ValueError("Se esperaba una coma entre transacciones.")
                position += 1
                while position < len(buffer) and buffer[position].isspace():
                    position += 1
            first = False

            while True:
                try:
                    item, end = decoder.raw_decode(buffer, position)
                    break
                except json.JSONDecodeError:
                    if eof:
                        raise ValueError("Transacción JSON incompleta o inválida.")
                    if position:
                        buffer = buffer[position:]
                        position = 0
                    fill()
            if not isinstance(item, dict):
                raise ValueError("Cada elemento del arreglo debe ser un objeto JSON.")
            yield item
            position = end
            if position >= READ_SIZE:
                buffer = buffer[position:]
                position = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    count = 0
    with tempfile.TemporaryDirectory(prefix=".transactions-", dir=args.output) as temp_dir:
        output = None
        try:
            for transaction in json_array_items(args.input):
                if count % RECORDS_PER_PART == 0:
                    if output:
                        output.close()
                    part = count // RECORDS_PER_PART
                    output = open(os.path.join(temp_dir, f"part-{part:05d}.jsonl"),
                                  "w", encoding="utf-8")
                output.write(json.dumps(transaction, ensure_ascii=False, separators=(",", ":")) + "\n")
                count += 1
        finally:
            if output:
                output.close()

        if count == 0:
            raise ValueError("El dataset no contiene transacciones.")
        for old_part in glob.glob(os.path.join(args.output, "part-*.jsonl")):
            os.remove(old_part)
        for name in os.listdir(temp_dir):
            os.replace(os.path.join(temp_dir, name), os.path.join(args.output, name))
    print(f"[ok] {count} transacciones preparadas en {args.output}")


if __name__ == "__main__":
    main()
