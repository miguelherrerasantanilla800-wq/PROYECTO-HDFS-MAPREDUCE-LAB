#!/bin/bash
# Arranca el daemon indicado en primer plano (los logs salen por `docker logs`).
set -e
case "$1" in
  namenode)
    if [ ! -f /hadoop-data/name/current/VERSION ]; then
      echo ">>> Formateando NameNode (primera vez)"
      hdfs namenode -format -force -nonInteractive
    fi
    exec hdfs namenode ;;
  datanode)         exec hdfs datanode ;;
  resourcemanager)  exec yarn resourcemanager ;;
  nodemanager)      exec yarn nodemanager ;;
  historyserver)    exec mapred historyserver ;;
  *)                exec "$@" ;;
esac
