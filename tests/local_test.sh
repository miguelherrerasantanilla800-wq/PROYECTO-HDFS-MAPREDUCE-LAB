#!/usr/bin/env bash
# Prueba SIN Hadoop con el dataset real: simula Hadoop Streaming usando sort local.
# Requiere Python 3 y el JSON junto al directorio del proyecto.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
PY=$(command -v python3 || command -v python)
D=${DATA_DIR:-data_local_test}; R=results_local
DATASET=${TRANSACTIONS_JSON:-../dataset_transacciones_1_millon.json}
mkdir -p "$R" "$D"
$PY scripts/prepare_transactions.py --input "$DATASET" --output "$D/transactions"
export LC_ALL=C           # Hadoop ordena por bytes; sort con LC_ALL=C hace lo mismo
S() { sort -t$'\t' -k1,1; }
J=jobs/transactions
export PYTHONPATH="$PWD/$J${PYTHONPATH:+:$PYTHONPATH}"

cat "$D"/transactions/*.jsonl | $PY $J/avg_by_category/mapper.py 2>/dev/null | S | $PY $J/avg_by_category/combiner.py | S | $PY $J/avg_by_category/reducer.py > $R/avg_by_category.tsv
cat "$D"/transactions/*.jsonl | $PY $J/peak_hours/mapper.py 2>/dev/null | S | $PY jobs/common/sum_reducer.py > $R/peak_hours.tsv
cat "$D"/transactions/*.jsonl | $PY $J/top_merchants/mapper.py 2>/dev/null | S | $PY jobs/common/sum_reducer.py | S | TOP_N=10 $PY $J/top_merchants/reducer.py > $R/top_merchants.tsv
cat "$D"/transactions/*.jsonl | $PY $J/fraud_by_city/mapper.py 2>/dev/null | S | $PY $J/fraud_by_city/combiner.py | S | $PY $J/fraud_by_city/reducer.py > $R/fraud_by_city.tsv
cat "$D"/transactions/*.jsonl | $PY $J/payment_methods/mapper.py 2>/dev/null | S | $PY $J/payment_methods/reducer.py > $R/payment_methods.tsv

for name in avg_by_category peak_hours top_merchants fraud_by_city payment_methods; do
  add_result_header "$name" "$R/$name.tsv"
done

$PY scripts/validate.py --data "$D" --results "$R"
