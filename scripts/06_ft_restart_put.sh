#!/usr/bin/env bash
# EXPERIMENTO C - Reiniciar un DataNode DURANTE una escritura en HDFS (pipeline recovery).
# Sube un archivo grande con bloques pequeños y reinicia datanode3 a mitad. Comprueba integridad por checksum.
# Uso: 06_ft_restart_put.sh [tamaño_MB=300]
source "$(dirname "$0")/lib.sh"
SIZE=${1:-300}
log "Creando archivo de ${SIZE} MB dentro del NameNode (/tmp/big.bin)"
nnsh "head -c ${SIZE}M /dev/urandom > /tmp/big.bin"
LOCAL=$(nnsh "md5sum < /tmp/big.bin"); echo "md5(local) = $LOCAL"
nn hdfs dfs -rm -f -skipTrash /lab/big.bin >/dev/null 2>&1 || true

log "Subiendo a HDFS en segundo plano (bloques de 4 MB para tener muchos pipelines)"
nnsh "hdfs dfs -D dfs.blocksize=4194304 -put /tmp/big.bin /lab/big.bin" > results/ft_put.log 2>&1 &
PUTPID=$!
sleep 3
log "FALLA: docker restart datanode3 durante la escritura"
docker restart datanode3 >/dev/null
wait $PUTPID; echo "hdfs put terminó con código $?"
echo "--- mensajes del cliente (recuperación de pipeline):"; tail -n 5 results/ft_put.log

wait_cluster 3 any >/dev/null 2>&1 || true; sleep 15
log "Integridad"
REMOTE=$(nnsh "hdfs dfs -cat /lab/big.bin | md5sum"); echo "md5(HDFS)  = $REMOTE"
[ "$LOCAL" = "$REMOTE" ] && ok "Archivo íntegro: la escritura sobrevivió al reinicio" || warn "CHECKSUM DISTINTO"
nn hdfs fsck /lab/big.bin | grep -E "Status|Under-replicated|Over-replicated|Corrupt|Average block replication"
nn hdfs dfs -rm -f -skipTrash /lab/big.bin >/dev/null; nnsh "rm -f /tmp/big.bin"
