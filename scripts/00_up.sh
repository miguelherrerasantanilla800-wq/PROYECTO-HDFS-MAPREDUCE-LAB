#!/usr/bin/env bash
# Construye la imagen, levanta los 8 contenedores y espera a que el clúster esté sano.
source "$(dirname "$0")/lib.sh"
mkdir -p data results && chmod 777 data results      # el usuario 'hadoop' del contenedor debe poder escribir
log "docker compose up (la primera vez descarga Hadoop ~700 MB)"
docker compose up -d --build
wait_cluster 3 2
docker compose ps
cat <<MSG

UIs:  HDFS http://localhost:9870   YARN http://localhost:8088   History http://localhost:19888
MSG
