#!/usr/bin/env bash
# Ejecuta en orden los cinco análisis MapReduce de transacciones.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
FAILED=()

for name in avg_by_category peak_hours top_merchants fraud_by_city payment_methods; do
  if ! bash scripts/run_transaction_job.sh "$name"; then
    warn "$name FALLÓ"
    FAILED+=("$name")
  fi
done

log "Resumen"
if [ ${#FAILED[@]} -ne 0 ]; then
  warn "Fallaron: ${FAILED[*]}"
  exit 1
fi

ok "5/5 jobs SUCCEEDED"
echo; echo "Horas pico (top 3):"; sort -t$'\t' -k2,2nr results/peak_hours.tsv | head -3
echo; echo "Top 5 comercios:"; head -5 results/top_merchants.tsv
echo; echo "Promedio por categoría:"; column -t -s$'\t' results/avg_by_category.tsv 2>/dev/null || cat results/avg_by_category.tsv
echo; echo "Fraude por ciudad:"; cat results/fraud_by_city.tsv
echo; echo "Métodos de pago:"; cat results/payment_methods.tsv
