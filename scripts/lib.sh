#!/usr/bin/env bash
# Funciones comunes. Se usa con:  source scripts/lib.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export MSYS_NO_PATHCONV=1          # Git Bash (Windows): evita que /lab/... se convierta en C:/Program Files/...
STREAMING_JAR='/opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar'
HDFS_IN=/lab/input
HDFS_OUT=/lab/output

nn() {
  if [ "${HADOOP_CONTAINER_LOCAL:-0}" = 1 ]; then "$@"; else docker exec namenode "$@"; fi
}
nnsh() {
  if [ "${HADOOP_CONTAINER_LOCAL:-0}" = 1 ]; then bash -c "$1"; else docker exec namenode bash -c "$1"; fi
}
log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

live_dns()  { nn hdfs dfsadmin -report 2>/dev/null | sed -n 's/^Live datanodes (\([0-9]*\)).*/\1/p' | head -1; }
dead_dns()  { nn hdfs dfsadmin -report 2>/dev/null | sed -n 's/^Dead datanodes (\([0-9]*\)).*/\1/p' | head -1; }
running_nms() { nn yarn node -list 2>/dev/null | grep -c 'RUNNING' || true; }

# Espera a que haya N DataNodes vivos y M NodeManagers RUNNING (por defecto 3 y 2)
wait_cluster() {
  local want_dn=${1:-3} want_nm=${2:-2} t=0     # want_nm="any" -> no exige NodeManagers
  log "Esperando clúster ($want_dn DataNodes, $want_nm NodeManagers)..."
  until [ "$(live_dns || true)" = "$want_dn" ] && { [ "$want_nm" = any ] || [ "$(running_nms)" = "$want_nm" ]; }; do
    sleep 5; t=$((t+5))
    printf '.'; [ $t -ge 240 ] && { echo; warn "Timeout. Revisa: docker compose logs"; return 1; }
  done
  echo; nn hdfs dfsadmin -safemode wait >/dev/null
  ok "Clúster listo en ~${t}s"
}

app_id_by_name() { nn yarn application -list -appStates "${2:-RUNNING}" 2>/dev/null | awk -v n="$1" '$0 ~ n {print $1; exit}'; }
