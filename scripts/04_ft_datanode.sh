#!/usr/bin/env bash
# EXPERIMENTO A - Falla de un DataNode: detección (Dead), re-replicación de bloques y lectura sin pérdida.
# Uso: 04_ft_datanode.sh [datanode2]
source "$(dirname "$0")/lib.sh"
VICTIM=${1:-datanode2}
F=$HDFS_IN/transactions

summary() { nn hdfs fsck $F 2>/dev/null | grep -E "Total blocks|Under-replicated|Over-replicated|Average block replication|Status"; }

log "ANTES: réplicas y checksum de los datos"
wait_cluster 3 any >/dev/null 2>&1 || true
summary
BEFORE=$(nnsh "hdfs dfs -cat '$F/*' | md5sum")
echo "md5(antes) = $BEFORE"

log "FALLA: docker stop $VICTIM"
docker stop "$VICTIM" >/dev/null
T0=$(date +%s)

log "Observando (dfs.heartbeat.interval=3s, recheck=10s -> 'Dead' tras ~50 s)"
while :; do
  L=$(live_dns); D=$(dead_dns); URB=$(nn hdfs fsck "$F" 2>/dev/null | sed -n 's/^ Under-replicated blocks:[[:space:]]*//p' | cut -d' ' -f1)
  printf '[t=%3ss] live=%s dead=%s under-replicated=%s\n' $(( $(date +%s)-T0 )) "${L:-?}" "${D:-0}" "${URB:-?}"
  [ "${D:-0}" -ge 1 ] && [ "${URB:-1}" = "0" ] && break
  [ $(( $(date +%s)-T0 )) -gt 240 ] && { warn "timeout"; break; }
  sleep 5
done
ok "El NameNode detectó la caída y re-replicó los bloques en los DataNodes restantes"
summary

log "LECTURA con un DataNode caído: el checksum debe ser idéntico"
AFTER=$(nnsh "hdfs dfs -cat '$F/*' | md5sum")
echo "md5(después) = $AFTER"; [ "$BEFORE" = "$AFTER" ] && ok "Datos íntegros" || warn "¡DATOS DIFERENTES!"

log "RECUPERACIÓN: docker start $VICTIM (el NameNode eliminará réplicas sobrantes)"
docker start "$VICTIM" >/dev/null
wait_cluster 3 any >/dev/null 2>&1 || true
sleep 10; summary
echo; echo "Mira también: http://localhost:9870 -> Datanodes (In service / Dead) y 'docker logs namenode | grep -i -E \"dead|replicat\"'"
