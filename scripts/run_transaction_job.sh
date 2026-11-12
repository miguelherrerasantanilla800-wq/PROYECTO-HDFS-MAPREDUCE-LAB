#!/usr/bin/env bash
# Ejecuta un único análisis sobre las transacciones y copia su salida a ./results.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
J=file:///lab/jobs
name=${1:?Uso: run_transaction_job.sh <nombre-del-job>}

run_job() {
  log "JOB: $name"
  nn hdfs dfs -rm -r -f -skipTrash "$HDFS_OUT/$name" >/dev/null 2>&1 || true
  nn hadoop jar "$STREAMING_JAR" -D mapreduce.job.name="lab-$name" "$@" \
    -output "$HDFS_OUT/$name"
  nnsh "hdfs dfs -cat '$HDFS_OUT/$name/part-*' > /lab/results/$name.tsv"
  ok "$name -> results/$name.tsv  ($(wc -l < "results/$name.tsv") líneas)"
}

case "$name" in
  avg_by_category)
    run_job \
      -D mapreduce.job.reduces=2 \
      -files "$J/transactions/common.py,$J/transactions/avg_by_category/mapper.py,$J/transactions/avg_by_category/combiner.py,$J/transactions/avg_by_category/reducer.py" \
      -input "$HDFS_IN/transactions" \
      -mapper "python3 mapper.py" -combiner "python3 combiner.py" -reducer "python3 reducer.py" \
      -cmdenv PYTHONPATH=.
    ;;
  peak_hours)
    run_job \
      -D mapreduce.job.reduces=1 \
      -files "$J/transactions/common.py,$J/transactions/peak_hours/mapper.py,$J/common/sum_reducer.py" \
      -input "$HDFS_IN/transactions" \
      -mapper "python3 mapper.py" -combiner "python3 sum_reducer.py" -reducer "python3 sum_reducer.py" \
      -cmdenv PYTHONPATH=.
    ;;
  top_merchants)
    run_job \
      -D mapreduce.job.reduces=1 \
      -files "$J/transactions/common.py,$J/transactions/top_merchants/mapper.py,$J/common/sum_reducer.py,$J/transactions/top_merchants/reducer.py" \
      -input "$HDFS_IN/transactions" \
      -mapper "python3 mapper.py" -combiner "python3 sum_reducer.py" -reducer "python3 reducer.py" \
      -cmdenv PYTHONPATH=. -cmdenv TOP_N=10
    ;;
  fraud_by_city)
    run_job \
      -D mapreduce.job.reduces=1 \
      -files "$J/transactions/common.py,$J/transactions/fraud_by_city/mapper.py,$J/transactions/fraud_by_city/combiner.py,$J/transactions/fraud_by_city/reducer.py" \
      -input "$HDFS_IN/transactions" \
      -mapper "python3 mapper.py" -combiner "python3 combiner.py" -reducer "python3 reducer.py" \
      -cmdenv PYTHONPATH=.
    ;;
  payment_methods)
    run_job \
      -D mapreduce.job.reduces=1 \
      -files "$J/transactions/common.py,$J/transactions/payment_methods/mapper.py,$J/transactions/payment_methods/reducer.py" \
      -input "$HDFS_IN/transactions" \
      -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
      -cmdenv PYTHONPATH=.
    ;;
  *)
    echo "Análisis desconocido: $name" >&2
    exit 2
    ;;
esac
