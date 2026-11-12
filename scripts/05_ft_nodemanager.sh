#!/usr/bin/env bash
# EXPERIMENTO B - Falla de un NodeManager con un job EN EJECUCIÓN (Map/Reduce interrumpido).
# Lanza un conteo lento sobre las transacciones, mata un NodeManager y observa:
# nodo LOST (30 s), tareas reprogramadas en el nodo sano, contadores de tareas killed/relanzadas y estado final.
# Uso: 05_ft_nodemanager.sh [--kill-am] [SLEEP_PER_LINE=0.005]
source "$(dirname "$0")/lib.sh"
KILL_AM=0; PAUSE=0.005
for a in "$@"; do case $a in --kill-am) KILL_AM=1;; *) PAUSE=$a;; esac; done
OUT=$HDFS_OUT/ft_slow_wordcount
LOGF=results/ft_slow_job.log

nn hdfs dfs -rm -r -f -skipTrash $OUT >/dev/null 2>&1 || true
log "Lanzando job lento en segundo plano (log: $LOGF)"
nn hadoop jar "$STREAMING_JAR" -D mapreduce.job.name=lab-ft-slow \
  -D mapreduce.job.reduces=2 \
  -files file:///lab/jobs/slow_wordcount/mapper.py,file:///lab/jobs/common/sum_reducer.py \
  -input $HDFS_IN/transactions -output $OUT \
  -mapper "python3 mapper.py" -combiner "python3 sum_reducer.py" -reducer "python3 sum_reducer.py" \
  -cmdenv SLEEP_PER_LINE=$PAUSE > "$LOGF" 2>&1 &
JOBPID=$!

log "Esperando que el job esté RUNNING..."
for i in $(seq 1 30); do APP=$(app_id_by_name lab-ft-slow RUNNING); [ -n "$APP" ] && break; sleep 3; done
[ -z "$APP" ] && { warn "No apareció el job. Mira $LOGF"; exit 1; }
ok "Aplicación: $APP"; sleep 35   # dejar que arranquen los Map

AMHOST=$(nn yarn application -status "$APP" 2>/dev/null | grep -o 'nodemanager[0-9]' | head -1)
echo "ApplicationMaster en: ${AMHOST:-desconocido}"
if [ $KILL_AM -eq 1 ]; then VICTIM=${AMHOST:-nodemanager1}; else VICTIM=$([ "$AMHOST" = nodemanager1 ] && echo nodemanager2 || echo nodemanager1); fi

log "FALLA: docker kill $VICTIM  (caída abrupta mientras corren los Map)"
docker kill "$VICTIM" >/dev/null; T0=$(date +%s)

log "Observando estado del nodo y progreso del job"
while kill -0 $JOBPID 2>/dev/null; do
  S=$(nn yarn node -list -all 2>/dev/null | awk -v v="$VICTIM" '$1 ~ v {print $2}' | head -1)
  P=$(nn yarn application -status "$APP" 2>/dev/null | awk -F' : ' '/Progress/{print $2}')
  printf '[t=%3ss] %s=%s  job_progress=%s\n' $(( $(date +%s)-T0 )) "$VICTIM" "${S:-?}" "${P:-?}"
  sleep 10
done
wait $JOBPID; RC=$?

log "RESULTADO"
nn yarn application -status "$APP" 2>/dev/null | grep -E "State|Final-State|Application-Name"
echo "--- Contadores relevantes del log del cliente:"
grep -E "Launched map tasks|Launched reduce tasks|Killed map tasks|Killed reduce tasks|Failed map|Data-local|Rack-local" "$LOGF" || true
echo "--- Mensajes de reintento en el log:"
grep -E "Task Id|attempt_|TaskAttempt|Container .* (lost|released)|LOST" "$LOGF" | head -15 || true
[ $RC -eq 0 ] && ok "El job TERMINÓ con éxito pese a perder $VICTIM" || warn "El job terminó con código $RC"

log "RECUPERACIÓN: docker start $VICTIM"
docker start "$VICTIM" >/dev/null
wait_cluster 3 2 || true
nn yarn node -list -all
