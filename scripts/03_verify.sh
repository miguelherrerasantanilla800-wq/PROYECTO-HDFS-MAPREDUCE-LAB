#!/usr/bin/env bash
# Verificación de la ejecución: salud de HDFS/YARN, estado de cada job, logs, salidas y validación de resultados.
source "$(dirname "$0")/lib.sh"

log "1. Contenedores"
docker compose ps --format 'table {{.Name}}\t{{.Status}}'

log "2. HDFS: resumen (DataNodes vivos/muertos, capacidad, bloques)"
nn hdfs dfsadmin -report | grep -E "^(Configured Capacity|DFS Used|Under replicated|Blocks with corrupt|Missing blocks|Live datanodes|Dead datanodes)|^Name:|^Hostname:"

log "3. HDFS: salud del sistema de archivos (fsck)"
nn hdfs fsck / 2>/dev/null | grep -E "Status|Total size|Total files|Total blocks|Under-replicated|Mis-replicated|Corrupt|Average block replication|Number of data-nodes"

log "4. YARN: NodeManagers (RUNNING / LOST / UNHEALTHY ...)"
nn yarn node -list -all

log "5. YARN: aplicaciones y estado final (SUCCEEDED / FAILED / KILLED)"
nn yarn application -list -appStates ALL 2>/dev/null | cut -c1-150

log "6. Salidas en HDFS"
nn hdfs dfs -ls -R $HDFS_OUT

log "7. Logs agregados del último job terminado (primeras líneas)"
LAST=$(nn yarn application -list -appStates FINISHED 2>/dev/null | awk '/^application_/{print $1}' | tail -1)
if [ -n "$LAST" ]; then echo "Aplicación: $LAST"; nn yarn logs -applicationId "$LAST" 2>/dev/null | head -n 30
else warn "No hay aplicaciones terminadas todavía (¿corriste 02_run_jobs.sh?)"; fi

log "8. Validación independiente de resultados (Python puro vs salida MapReduce)"
nn python3 /lab/scripts/validate.py --data /lab/data --results /lab/results
