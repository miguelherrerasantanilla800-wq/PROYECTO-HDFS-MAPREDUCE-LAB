#!/usr/bin/env bash
# Prepara el JSON recibido y lo sube a HDFS.
source "$(dirname "$0")/lib.sh"

log "Convirtiendo el arreglo JSON a partes JSONL paralelizables"
nn python3 /lab/scripts/prepare_transactions.py \
  --input /lab/source/dataset_transacciones_1_millon.json \
  --output /lab/data/transactions

log "Creando estructura en HDFS: $HDFS_IN/transactions"
nn hdfs dfs -mkdir -p "$HDFS_IN/transactions" "$HDFS_OUT"

# Cada parte (~24 MB) queda en varios bloques, evitando cientos de tareas Map diminutas.
PUT="hdfs dfs -D dfs.blocksize=16777216 -put -f"
nnsh "$PUT /lab/data/transactions/part-*.jsonl $HDFS_IN/transactions/"

log "Contenido de HDFS"
nn hdfs dfs -ls -R -h $HDFS_IN
log "Bloques y réplicas de un archivo (fsck)"
nn hdfs fsck "$HDFS_IN/transactions/part-00000.jsonl" -files -blocks -locations | head -n 25
